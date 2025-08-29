from sqlalchemy import create_engine
import pandas as pd
from loguru import logger
from sql_queries.sheet1 import first_sql_map
from config.settings import CONNECTION_URI, DB_DATABASE, DB_SERVER


tab_logger = logger.bind(tab="Tab1")

def get_tab1_results():
    """Execute all SQL queries and return results as dictionary of DataFrames"""
    tab_logger.info("Starting database connection and query execution")
    
    try:
        engine = create_engine(CONNECTION_URI)
        tab_logger.info(f"Successfully connected to database: {DB_DATABASE} on server: {DB_SERVER}")
    except Exception as e:
        tab_logger.error(f"Failed to create database engine: {e}")
        return {}
    
    results = {}
    successful_queries = 0
    failed_queries = 0
    
    for key, query in first_sql_map.items():
        try:
            tab_logger.info(f"Executing query: {key}")
            df = pd.read_sql(query, engine)
            results[key] = df
            successful_queries += 1
            tab_logger.success(f"Query {key} executed successfully. Rows returned: {len(df)}")
        except Exception as e:
            failed_queries += 1
            tab_logger.error(f"Error executing query {key}: {e}")
            results[key] = pd.DataFrame()  # Return empty DataFrame on failure
    
    # Log summary
    tab_logger.info(f"Query execution completed. Successful: {successful_queries}, Failed: {failed_queries}")
    
    # Close the connection
    try:
        engine.dispose()
        tab_logger.info("Database connection closed successfully")
    except Exception as e:
        tab_logger.warning(f"Error while closing database connection: {e}")
    
    return results

    
