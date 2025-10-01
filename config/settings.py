import os

# GenAI configuration
# It is recommended to set the GOOGLE_API_KEY as an environment variable
# For example: export GOOGLE_API_KEY="your_api_key"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
MODEL_NAME = os.environ.get("GENAI_MODEL_NAME", "gemini-1.0-pro")

# Database configuration (defaults match current code; override via env vars)
# For example: export DB_SERVER="your_db_server"
DB_SERVER = os.environ.get("DB_SERVER", "localhost")
DB_DATABASE = os.environ.get("DB_DATABASE", "Master")
DB_USERNAME = os.environ.get("DB_USERNAME", "SA")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "MyStrongPass123")
ODBC_DRIVER = os.environ.get("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")

# SQLAlchemy connection URI
CONNECTION_URI = (
    f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}"
    f"?driver={ODBC_DRIVER.replace(' ', '+')}"
)