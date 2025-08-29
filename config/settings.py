import os

# GenAI configuration
GOOGLE_API_KEY = "AIzaSyArAuKljjmRWYVkZ2ng9OHgUqtJuUuZ5uU"
MODEL_NAME = os.environ.get("GENAI_MODEL_NAME", "gemini-2.0-flash")

# Database configuration (defaults match current code; override via env vars)
DB_SERVER = os.environ.get("DB_SERVER", "192.168.0.45,1433")
DB_DATABASE = os.environ.get("DB_DATABASE", "ExcelData")
DB_USERNAME = os.environ.get("DB_USERNAME", "user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "suggestme7725apassword")
ODBC_DRIVER = os.environ.get("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")

# SQLAlchemy connection URI
CONNECTION_URI = (
    f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}/{DB_DATABASE}"
    f"?driver={ODBC_DRIVER.replace(' ', '+')}"
)

