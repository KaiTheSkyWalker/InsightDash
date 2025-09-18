from __future__ import annotations

from typing import Dict, Any
import pandas as pd


def _is_datetime(s: pd.Series) -> bool:
    try:
        return pd.api.types.is_datetime64_any_dtype(s)
    except Exception:
        return False


def _is_bool(s: pd.Series) -> bool:
    try:
        return pd.api.types.is_bool_dtype(s)
    except Exception:
        return False


def _is_numeric(s: pd.Series) -> bool:
    try:
        return pd.api.types.is_numeric_dtype(s)
    except Exception:
        return False


def describe_by_column(df: pd.DataFrame, max_top: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Compute a robust, column-wise summary similar to pandas.describe() for every
    column, handling numeric, categorical, boolean and datetime types.

    Returns a dict keyed by column with a compact set of statistics. This is
    designed to be embedded in prompts as authoritative, model-agnostic facts.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {}

    out: Dict[str, Dict[str, Any]] = {}

    for col in df.columns:
        s = df[col]
        n_total = int(len(s))
        n_missing = int(s.isna().sum())
        base: Dict[str, Any] = {
            "dtype": str(s.dtype),
            "count": int(s.count()),
            "missing": n_missing,
        }

        if _is_numeric(s):
            desc = s.describe(percentiles=[0.25, 0.5, 0.75])
            base.update(
                {
                    "min": _to_num(desc.get("min")),
                    "p25": _to_num(desc.get("25%")),
                    "median": _to_num(desc.get("50%")),
                    "p75": _to_num(desc.get("75%")),
                    "max": _to_num(desc.get("max")),
                    "mean": _to_num(desc.get("mean")),
                    "std": _to_num(desc.get("std")),
                }
            )
        elif _is_datetime(s):
            try:
                s_dt = pd.to_datetime(s, errors="coerce")
            except Exception:
                s_dt = pd.to_datetime(pd.Series([], dtype="datetime64[ns]"))
            base.update(
                {
                    "min": _to_str(s_dt.min()),
                    "max": _to_str(s_dt.max()),
                }
            )
        elif _is_bool(s):
            vc = s.value_counts(dropna=True)
            base.update(
                {
                    "true": int(vc.get(True, 0)),
                    "false": int(vc.get(False, 0)),
                }
            )
        else:
            # Treat as categorical/text; record only counts and missing — omit 'top'/'unique' per request
            total_non_na = int((~s.isna()).sum())
            base.update({
                "non_null": total_non_na,
            })

        out[str(col)] = base

    return out



## Grouped statistics helpers were introduced and later reverted per request.
def _numeric_columns(df: pd.DataFrame) -> list:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []
    cols = []
    for c in df.columns:
        try:
            if _is_numeric(df[c]):
                cols.append(c)
        except Exception:
            pass
    return cols


def group_extents_by(df: pd.DataFrame, group_col: str, cols: list[str] | None = None) -> Dict[str, Dict[str, Any]]:
    """
    Compute min/max/mean/range per numeric column for each unique value of `group_col`.
    Returns {group_value: {col: {min, max, mean, range, count}}}
    """
    if not isinstance(df, pd.DataFrame) or df.empty or group_col not in df.columns:
        return {}
    cols = cols or _numeric_columns(df)
    if not cols:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    try:
        gb = df.groupby(group_col, dropna=False)
        for gval, sub in gb:
            per_col: Dict[str, Any] = {}
            for c in cols:
                s = sub[c]
                if not _is_numeric(s):
                    continue
                try:
                    mn = float(s.min()) if s.size else None
                    mx = float(s.max()) if s.size else None
                    mean = float(s.mean()) if s.size else None
                except Exception:
                    mn = mx = mean = None
                rng = (mx - mn) if (mn is not None and mx is not None) else None
                per_col[str(c)] = {
                    "min": _round(mn),
                    "max": _round(mx),
                    "mean": _round(mean),
                    "range": _round(rng),
                    "count": int(s.count()),
                }
            out[_to_str(gval)] = per_col
        return out
    except Exception:
        return {}


def grouped_stats_selected(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute grouped statistics for commonly-used dimensions if present:
    - outlet_category (or Category)
    - outlet_type
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return {}
    result: Dict[str, Any] = {}
    # Month (from multi-month combination)
    if "Month" in df.columns:
        result["Month"] = group_extents_by(df, "Month")
    # outlet_category alias
    cat_col = "outlet_category" if "outlet_category" in df.columns else ("Category" if "Category" in df.columns else None)
    if cat_col:
        result["outlet_category"] = group_extents_by(df, cat_col)
    # outlet_type
    if "outlet_type" in df.columns:
        result["outlet_type"] = group_extents_by(df, "outlet_type")
    return result

def _to_num(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def _round(x: float | None, ndigits: int = 2):
    if x is None:
        return None
    try:
        return round(float(x), ndigits)
    except Exception:
        return x


def _fmt(x: Any) -> Any:
    if isinstance(x, float):
        return _round(x)
    return x


def _to_str(x: Any) -> str:
    if x is None:
        return "None"
    try:
        return str(x)
    except Exception:
        return "<unrepr>"


# --- Month/category mix utilities ---
def category_mix_by_month(
    df: pd.DataFrame,
    month_col: str = "Month",
    category_col_main: str = "outlet_category",
    category_col_alt: str = "Category",
) -> pd.DataFrame:
    """
    Compute per-month category counts and percentage mix (A/B/C/D) from a
    detailed outlet-level DataFrame that includes a month column.

    Returns a DataFrame with columns: Month, category, count, pct
    """
    if not isinstance(df, pd.DataFrame) or df.empty or month_col not in df.columns:
        return pd.DataFrame(columns=[month_col, "category", "count", "pct"])
    cat_col = (
        category_col_main
        if category_col_main in df.columns
        else (category_col_alt if category_col_alt in df.columns else None)
    )
    if not cat_col:
        return pd.DataFrame(columns=[month_col, "category", "count", "pct"])
    try:
        d = df[[month_col, cat_col]].dropna(subset=[cat_col]).copy()
    except Exception:
        return pd.DataFrame(columns=[month_col, "category", "count", "pct"])
    try:
        grp = (
            d.groupby([month_col, cat_col], dropna=False)
            .size()
            .reset_index(name="count")
        )
        # Normalize label to a unified 'category' column
        grp = grp.rename(columns={cat_col: "category"})
        totals = grp.groupby(month_col, dropna=False)["count"].transform("sum")
        grp["pct"] = (grp["count"] / totals) * 100.0
        return grp
    except Exception:
        return pd.DataFrame(columns=[month_col, "category", "count", "pct"])
