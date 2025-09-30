import os

# GenAI configuration
GOOGLE_API_KEY = "AIzaSyArAuKljjmRWYVkZ2ng9OHgUqtJuUuZ5uU"
MODEL_NAME = os.environ.get("GENAI_MODEL_NAME", "gemini-2.0-flash")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Database configuration (defaults match current code; override via env vars)
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

# Optional HTTP Basic Auth for Dash; edit the *_DEFAULT values to toggle locally
ENABLE_DASH_AUTH_DEFAULT = True  # set to False to disable auth without env vars
DASH_AUTH_USERNAME_DEFAULT = "admin"
DASH_AUTH_PASSWORD_DEFAULT = "123"

ENABLE_DASH_AUTH = _env_flag("ENABLE_DASH_AUTH", default=ENABLE_DASH_AUTH_DEFAULT)
DASH_AUTH_USERNAME = os.environ.get("DASH_AUTH_USERNAME", DASH_AUTH_USERNAME_DEFAULT)
DASH_AUTH_PASSWORD = os.environ.get("DASH_AUTH_PASSWORD", DASH_AUTH_PASSWORD_DEFAULT)
