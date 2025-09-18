from __future__ import annotations

import pandas as pd
from typing import Dict


def fill_numeric_nans(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    out = df.copy()
    try:
        num_cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
        if num_cols:
            out[num_cols] = out[num_cols].replace([float("inf"), float("-inf")], pd.NA).fillna(0)
    except Exception:
        pass
    return out


def has_real_rows(df: pd.DataFrame) -> bool:
    try:
        return (
            isinstance(df, pd.DataFrame)
            and not df.empty
            and not df.dropna(how="all").empty
        )
    except Exception:
        return False


def _drop_restore_all_na_for_concat(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Concatenate two non-empty DataFrames while avoiding pandas' FutureWarning
    about empty/all-NA columns dtype inference.

    Strategy:
    - Align on the union of columns.
    - Temporarily drop columns that are all-NA across both frames.
    - Concatenate, then restore the dropped columns as all-NA and reorder columns.

    This keeps rows/columns intact (no permanent removal) and avoids changing
    non-null values. Numeric NA handling is already done in fill_numeric_nans().
    """
    cols = a.columns.union(b.columns)
    a2 = a.reindex(columns=cols)
    b2 = b.reindex(columns=cols)

    # Temporarily drop columns that are all-NA within each input
    drop_a = [c for c in a2.columns if a2[c].isna().all()]
    drop_b = [c for c in b2.columns if b2[c].isna().all()]
    a3 = a2.drop(columns=drop_a, errors="ignore")
    b3 = b2.drop(columns=drop_b, errors="ignore")

    out = pd.concat([a3, b3], ignore_index=True)
    # Restore original union of columns and ordering
    return out.reindex(columns=cols)


def concat_valid(prev: pd.DataFrame | None, cur: pd.DataFrame | None) -> pd.DataFrame | None:
    if has_real_rows(prev) and has_real_rows(cur):
        try:
            return _drop_restore_all_na_for_concat(prev, cur)
        except Exception:
            return cur
    return cur if has_real_rows(cur) else prev


def combine_month_frames(
    monthly_datasets: Dict,
    months: list[str],
    tab_key: str,
) -> Dict[str, pd.DataFrame]:
    res: Dict[str, pd.DataFrame] = {}
    for label in months:
        src = (monthly_datasets or {}).get(label, {})
        tab = src.get(tab_key) or {}
        for k, df in (tab or {}).items():
            if not isinstance(df, pd.DataFrame):
                continue
            d2 = fill_numeric_nans(df.copy())
            d2["Month"] = label
            prev = res.get(k)
            combined = concat_valid(prev, d2)
            res[k] = combined if combined is not None else d2
    return res
