try:
    from sql_queries.sheet3 import third_sql_map  # type: ignore
except Exception:
    third_sql_map = {}
from .base import execute_queries

def get_tab3_results():
    """Execute all SQL queries and return results as dictionary of DataFrames"""
    return execute_queries(third_sql_map, "Tab3")