import pandas as pd


def uniq(series_list):
    """Union unique non-null values across multiple Series, preserving order via Index union."""
    vals = pd.Index([])
    for s in series_list:
        if s is not None:
            vals = vals.union(pd.Index(s.dropna().unique()))
    return list(vals)


def pack_df(df: pd.DataFrame, max_rows: int = 300):
    """Pack a DataFrame into a light dict for JSON transport and table preview."""
    recs = df.head(max_rows).to_dict('records')
    return {"columns": list(df.columns), "records": recs, "n_rows": int(len(df))}

