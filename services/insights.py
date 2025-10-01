from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple
import pandas as pd
from utils.df_summary import describe_by_column

from .llm import generate_markdown_from_prompt
from .prompts import (
    build_prompt_individual,
)


def _chunk_dataframe(df: pd.DataFrame, chunk_size: int = 400) -> List[pd.DataFrame]:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return [pd.DataFrame()]
    n = len(df)
    if n <= chunk_size:
        return [df]
    return [df.iloc[i : i + chunk_size].copy() for i in range(0, n, chunk_size)]


def _record_pack(df: pd.DataFrame) -> Dict:
    return {
        "columns": list(df.columns),
        "records": df.to_dict("records"),
        "n_rows": int(len(df)),
    }


def _call_llm(provider: str, prompt: str) -> Tuple[Optional[str], Optional[str]]:
    # Single provider path (Gemini)
    return generate_markdown_from_prompt(prompt)


def summarize_chart_via_chunks(
    *,
    graph_id: str,
    graph_label: str,
    df_full: pd.DataFrame,
    meta: Optional[dict],
    provider: str,
    context_text: str = "",
    focus_hint: str = "",
    per_chunk_prompt_builder: Optional[Callable[[dict, str, str], str]] = None,
    final_prompt_builder: Optional[Callable[[dict, str, str], str]] = None,
    chunk_size: int = 400,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Map-reduce style summarization for a single chart:
      1) Break the full DataFrame into row chunks.
      2) Generate a concise per-chunk summary using the individual prompt format.
      3) Aggregate all chunk summaries into a final per-chart analysis.

    Returns (final_markdown, error).
    """
    try:
        chunks = _chunk_dataframe(df_full, chunk_size=chunk_size)
        chunk_summaries: List[str] = []

        # Step 1/2: per-chunk summaries (map phase)
        for idx, cdf in enumerate(chunks, start=1):
            payload = {
                "graph_id": graph_id,
                "graph_label": graph_label,
                "metadata": meta or {},
                "columns": list(cdf.columns),
                "n_rows": int(len(cdf)),
                "rows": cdf.to_dict("records"),
                # Inform the model that this is a partition of a larger table
                "chunk_info": {"index": idx, "total": len(chunks)},
            }
            # Attach computed stats per chunk to minimize arithmetic by LLM
            try:
                payload["computed_stats"] = describe_by_column(cdf)
            except Exception:
                pass
            if per_chunk_prompt_builder:
                prompt = per_chunk_prompt_builder(payload, context_text, focus_hint)
            else:
                # Reuse the individual prompt; it already enforces quantified, concise outputs.
                prompt = build_prompt_individual(payload, context_text, focus_hint)

            text, err = _call_llm(provider, prompt)
            if err:
                return None, f"Chunk {idx} LLM error: {err}"
            chunk_summaries.append((text or "").strip())

        # Step 3: aggregate (reduce phase)
        aggregation_payload = {
            "graph_id": graph_id,
            "graph_label": graph_label,
            "metadata": meta or {},
            "chunk_count": len(chunks),
            "chunk_summaries": chunk_summaries,
        }

        # Precompute authoritative statistics over the full dataset
        try:
            full_stats = describe_by_column(df_full)
        except Exception:
            full_stats = {}
        if final_prompt_builder is not None:
            agg_prompt = final_prompt_builder(aggregation_payload, context_text, focus_hint)
        else:
            # Lightweight aggregator prompt: synthesize a single concise report
            # from per-chunk summaries, keeping the same output structure
            # expected by build_prompt_individual users.
            def _fmt_col(name: str, st: dict) -> str:
                missing = st.get("missing", 0)
                if {"min", "max", "mean"}.issubset(st.keys()):
                    return (
                        f"- {name}: min={st.get('min')}, p25={st.get('p25')}, median={st.get('median')}, "
                        f"p75={st.get('p75')}, max={st.get('max')}, mean={st.get('mean')}, std={st.get('std')} (missing={missing})"
                    )
                if "true" in st and "false" in st:
                    return f"- {name}: true={st.get('true')}, false={st.get('false')} (missing={missing})"
                if "unique" in st:
                    tops = st.get("top") or []
                    tops_s = ", ".join(
                        f"{t.get('value')}={t.get('count')} ({t.get('pct')}%)" for t in tops
                    )
                    return f"- {name}: unique={st.get('unique')}, top: {tops_s} (missing={missing})"
                if "min" in st and "max" in st:
                    return f"- {name}: min={st.get('min')}, max={st.get('max')} (missing={missing})"
                return f"- {name}: count={st.get('count', 0)} (missing={missing})"

            full_stats_text_lines = []
            if full_stats:
                full_stats_text_lines.append("COMPUTED STATISTICS (authoritative; full dataset):")
                for cname, cstats in full_stats.items():
                    try:
                        full_stats_text_lines.append(_fmt_col(cname, cstats))
                    except Exception:
                        pass
                full_stats_text_lines.append("")

            agg_prompt = (
                "You are a senior data analyst. Combine multiple partial summaries of the "
                f"same chart ('{graph_label}') into one coherent, non-duplicative analysis.\n"
                "- Each summary covers a different row chunk of the same dataset.\n"
                "- Keep only evidence-based, quantified statements that are supported across the full set.\n"
                "- Remove duplicate points and reconcile any conflicts conservatively.\n"
                "- Return clean markdown only (no code fences).\n\n"
                + (f"FOCUS HINT: {focus_hint}\n\n" if focus_hint else "")
                + ("\n".join(full_stats_text_lines) + "\n\n" if full_stats_text_lines else "")
                + ("")
                + "For the 'Observation' section, rely strictly on the computed statistics above; do not do your own arithmetic.\n\n"
                "Follow this structure strictly:\n"
                "### 1. Observation\n"
                "### 2. Interpretation\n"
                "### 3. Recommendation\n"
                "### Parameter Focus Coverage\n\n"
                f"Context/Purpose: {context_text}\n\n"
                "Summaries to synthesize (ordered):\n" + "\n\n".join(chunk_summaries)
            )

        final_text, final_err = _call_llm(provider, agg_prompt)
        if final_err:
            return None, final_err
        return (final_text or "").strip(), None
    except Exception as e:
        return None, str(e)


def synthesize_across_charts(
    *,
    chart_texts: List[Tuple[str, str]],  # (graph_label, markdown)
    provider: str,
    context_text: str = "",
    focus_hint: str = "",
) -> Tuple[Optional[str], Optional[str]]:
    """
    Combine multiple per-chart analyses into one integrated leadership-ready report.
    chart_texts: list of (label, text) after per-chart aggregation.
    Returns (markdown, error).
    """
    try:
        if not chart_texts:
            return "", None
        parts = []
        for label, text in chart_texts:
            parts.append(f"## {label}\n\n{text.strip()}")
        combined_source = "\n\n".join(parts)

        prompt = (
            "You are a senior data analyst presenting an integrated insights report to leadership.\n"
            "Synthesize the following per-chart analyses into one concise report, avoiding duplication: \n"
            "- Preserve quantified evidence and explicit parameter mentions.\n"
            "- Unify terminology and reconcile any conflicts conservatively.\n"
            "- Return clean markdown only.\n\n"
            + (f"FOCUS HINT: {focus_hint}\n\n" if focus_hint else "")
            + "Structure your integrated report as follows:\n\n"
            "## Executive Summary: The Core Narrative\n"
            "## Integrated Insights & Relationships (with numbers)\n"
            "## Strategic Implications & Risks\n"
            "## Top Data Evidence\n"
            "## Recommended Strategic Actions (with Reasons)\n\n"
            f"Context/Purpose: {context_text}\n\n"
            "Per-chart analyses to synthesize:\n\n"
            f"{combined_source}"
        )

        final_text, err = _call_llm(provider, prompt)
        if err:
            return None, err
        return (final_text or "").strip(), None
    except Exception as e:
        return None, str(e)
