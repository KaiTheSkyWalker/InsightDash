from typing import Dict, Tuple, Optional, List

import pandas as pd


KPI_COLS = [
    "new_car_reg_pct",
    "gear_up_ach_pct",
    "pov_pct",
    "ins_renew_1st_pct",
    "ins_renew_overall_pct",
    "intake_pct",
    "revenue_pct",
    "parts_pct",
    "lubricant_pct",
    "eappointment_pct",
    "nps_sales_pct",
    "cs_service_pct",
    "qpi_pct",
]


def get_filtered_frames(
    tab2: Dict[str, pd.DataFrame], filters: Dict
) -> Tuple[pd.DataFrame,]:
    """Filter Tab 2 dataset (Sheet 2 q1) based on global filters.

    Expected columns from sql_queries.sheet2.q1: rgn, outlet_name, outlet_type, outlet_category,
    rate_performance, rate_quality, total_score, rank_region, rank_nationwide, and KPI % columns.
    """
    df = tab2.get("q1", pd.DataFrame()).copy()
    if df.empty:
        return (df,)

    # Apply global filters
    regions = filters.get("regions") or []
    cats = filters.get("outlet_categories") or []
    types = filters.get("outlet_types") or []
    outlets = filters.get("outlets") or []
    search_text = (filters.get("search_text") or "").strip().lower()
    score_range = filters.get("score_range") or [0, 100]
    perf_range = filters.get("perf_range") or [0, 100]
    qual_range = filters.get("qual_range") or [0, 100]
    rreg = filters.get("rank_region") or [1, 999]
    rnw = filters.get("rank_nationwide") or [1, 999]

    def col(d: pd.DataFrame, names: List[str]) -> Optional[str]:
        return next((n for n in names if n in d.columns), None)

    rcol = col(df, ["rgn"])
    ocol = col(df, ["outlet_name"])
    tcol = col(df, ["outlet_type"])
    ccol = col(df, ["outlet_category"])

    if regions and rcol:
        # Exact match first; if no rows, try normalized (trim/casefold)
        d1 = df[df[rcol].isin(regions)]
        if d1.empty:
            try:
                tmp = df.copy()
                tmp["__r"] = tmp[rcol].astype(str).str.strip().str.casefold()
                rnorm = [str(x).strip().casefold() for x in regions]
                d1 = tmp[tmp["__r"].isin(rnorm)].drop(columns=["__r"])
            except Exception:
                d1 = df[df[rcol].isin(regions)]
        df = d1
    if cats and ccol:
        df = df[df[ccol].isin(cats)]
    if types and tcol:
        df = df[df[tcol].isin(types)]
    if outlets and ocol:
        df = df[df[ocol].isin(outlets)]
    if search_text and ocol:
        try:
            df = df[df[ocol].str.lower().str.contains(search_text, na=False)]
        except Exception:
            pass

    def clamp_range(df: pd.DataFrame, col: str, rng: List[float]):
        if col in df.columns and isinstance(rng, (list, tuple)) and len(rng) == 2:
            lo, hi = rng
            return df[(df[col] >= lo) & (df[col] <= hi)]
        return df

    df = clamp_range(df, "total_score", score_range)
    df = clamp_range(df, "rate_performance", perf_range)
    df = clamp_range(df, "rate_quality", qual_range)
    df = clamp_range(df, "rank_region", rreg)
    df = clamp_range(df, "rank_nationwide", rnw)

    return (df,)
