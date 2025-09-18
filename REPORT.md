# Perodua CR KPI Dashboard — Technical Report

## Overview
- Stack: Python 3.10, Dash/Plotly, pandas
- Purpose: Interactive analytics and LLM-generated insights for Customer Relations KPIs across outlets, regions, and outlet types.
- Tabs:
  - Tab 1: Performance & Quality by Region
  - Tab 2: Parameter Correlation (dynamic scatter)
  - Tab 3: Category & Type Diagnostics

## Core Data Flow
- Monthly data is provided via `monthly_datasets` with keys like `"March"`, `"May"` and per-tab dicts (`tab1`, `tab2`, `tab3`).
- When multiple months are selected, the app combines month frames per key (e.g., `q1`, `q4`) into a single DataFrame with a `Month` column for unified analysis.
- For insight generation with month comparison enabled, the app also passes per-month slices as separate DataFrames so the LLM can produce explicit comparisons.

## Recent Improvements
- Month comparison correctness across all tabs:
  - q2/q6: Use `category_mix_by_month` to build per-month mixes (Month, category, count, pct) for clear comparisons like “March A% > May A%”.
  - q1/q3: Provide per-month outlet-level slices for valid MoM analysis of region/outlet distributions.
  - Tab 3 (gaps): Per-month KPI gap tables added for B/C/D categories versus target 100.
- Provider simplification:
  - Removed OpenRouter/DeepSeek R1; Gemini is the only LLM path.
- Stability & UX:
  - Filled numeric NaNs with 0 during month combination to prevent propagation of missing values.
  - Excluded empty/all-NA frames before concat to silence pandas FutureWarnings and stabilize dtypes.
  - Consolidated Compare Months toggle to sidebar; removed the top-bar toggle. Added guards to only enable compare when 2+ months are selected. Eliminated callback cycles.

## Key Utilities
- `utils/df_summary.py`
  - `describe_by_column(df)`: dtype-aware stats for each column.
  - `grouped_stats_selected(df)`: grouped stats by Month/outlet_category/outlet_type when present.
  - `category_mix_by_month(df)`: month/category mix with counts and pct.
- `services/insights.py`
  - `summarize_chart_via_chunks(...)`: map-reduce across row chunks for large tables.
  - `synthesize_across_charts(...)`: merges per-chart markdown into a single narrative.

## Callback Architecture (high level)
- `filter-store` holds global filters (categories, regions, outlet types, months, compare flag).
- Graph callbacks pull combined month frames and apply filters to render charts.
- Selection callback captures selected charts and builds insight payloads.
- Insight callback generates one combined report or per-chart insights depending on mode, with explicit MoM comparison when relevant.

## DRY & Naming Recommendations
- DRY extraction (proposed):
  - `utils/dataframe.py`
    - `fill_numeric_nans(df)`: replace NaN/inf in numeric cols with 0
    - `has_real_rows(df)`: detect non-empty, non-all-NA frames
    - `concat_valid(prev, cur)`: safe concat that excludes invalid frames
    - `combine_month_frames(monthly_datasets, months, tab_key)`: shared month combiner
  - `utils/insights_data.py`
    - `month_slice_for_chart(chart_id, month_label, context, filters)` to unify month slicing across insight flows
  - `utils/stats_render.py`
    - `sanitize_stats`, `round_floats`, `preview_table` for consistent debug rendering
- Naming examples (incremental within touched code):
  - `gf` → `global_filters`, `lf` → `local_filters`
  - `gid` → `chart_id`, `base_df` → `chart_df`
  - `t1_q4_f` → `tab1_outlet_detail`, `t2_df_chart` → `tab2_scatter_data`
  - `_valid` → `has_real_rows`

## Known Constraints & Opportunities
- Constraints
  - Month multi-select remains in the top bar; compare toggle sits in the sidebar. Consider consolidating all month controls into the sidebar for clarity.
  - Some callbacks still contain complex inline logic (readability). Refactoring into utilities will aid maintenance and testing.
- Opportunities
  - Unit tests for month combining, `category_mix_by_month`, and month-slicing per chart.
  - Centralize preview/stats helpers and apply consistent formatting rules.
  - Inline docstrings and type hints for the core callbacks and utilities.

## Operational Notes
- Run (offline/dev): `DASH_OFFLINE=1 python app.py`
- Env vars: `GOOGLE_API_KEY`, `MODEL_NAME` (from `config/settings.py`)
- Logs: Prompts and metadata are written to `logs/insights_prompts.log` for traceability.

## Next Steps (Execution Plan)
1) Add shared utilities for month combination and month slicing; replace duplicate code in `app.py`.
2) Rename variables to improve readability in modified sections (keep interfaces stable to avoid regressions).
3) Extract debug preview/stats helpers and reuse across insight flows.
4) Optional: Move month multi-select into sidebar and remove top-bar month control.
5) Add lightweight unit tests for the new utilities.

## Appendix — Rationale for Key Changes
- Removing OpenRouter simplifies configuration, reduces branching, and avoids provider-specific failure modes.
- Numeric fill for NaNs makes aggregates and charts more stable when data is incomplete.
- Excluding empty/all-NA frames before concatenation prevents dtype drift in future pandas versions.
- Sidebar-only compare toggle with guards provides a clearer model for MoM comparison and avoids callback cycles.

