from sql_queries.sheet3 import build_third_sql_map
from .base import execute_queries

def get_tab3_results(table_name: str = "kpi_march"):
    """Execute all SQL queries and return results as dictionary of DataFrames

    table_name: target month table (e.g., 'kpi_march', 'kpi_may')
    """
    return execute_queries(build_third_sql_map(table_name), "Tab3")
