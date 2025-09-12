from sqlalchemy import create_engine
import pandas as pd
from loguru import logger
from config.settings import CONNECTION_URI, DB_DATABASE, DB_SERVER
from typing import Dict, Callable

def execute_queries(sql_map: Dict[str, str], tab_name: str, remap_logic: Callable[[Dict[str, pd.DataFrame]], Dict[str, pd.DataFrame]] = None):
    """Execute SQL queries and return results as a dictionary of DataFrames."""
    tab_logger = logger.bind(tab=tab_name)
    tab_logger.info("Starting database connection and query execution")

    try:
        engine = create_engine(CONNECTION_URI)
        tab_logger.info(
            f"Successfully connected to database: {DB_DATABASE} on server: {DB_SERVER}"
        )
    except Exception as e:
        tab_logger.error(f"Failed to create database engine: {e}")
        return {}

    results: dict[str, pd.DataFrame] = {}
    successful_queries = 0
    failed_queries = 0

    for key, query in sql_map.items():
        try:
            tab_logger.info(f"Executing query: {key}")
            df = pd.read_sql(query, engine)
            results[key] = df
            successful_queries += 1
            tab_logger.success(
                f"Query {key} executed successfully. Rows returned: {len(df)}"
            )
        except Exception as e:
            failed_queries += 1
            tab_logger.error(f"Error executing query {key}: {e}")
            results[key] = pd.DataFrame()  # Return empty DataFrame on failure

    if remap_logic:
        results = remap_logic(results)

    # Log summary
    tab_logger.info(
        f"Query execution completed. Successful: {successful_queries}, Failed: {failed_queries}"
    )

    # Close the connection
    try:
        engine.dispose()
        tab_logger.info("Database connection closed successfully")
    except Exception as e:
        tab_logger.warning(f"Error while closing database connection: {e}")

    return results
