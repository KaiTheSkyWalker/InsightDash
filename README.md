# InsightDash

InsightDash is a multi-tab Dash application for visualizing and analyzing Key Performance Indicators (KPIs). It features interactive charts and leverages Google's Gemini AI to generate data-driven insights.

## Features

- **Multi-tab Dashboard:** Explore different aspects of your data through organized tabs.
- **Interactive Visualizations:** Utilize Plotly charts for a dynamic and engaging user experience.
- **AI-Powered Insights:** Generate summaries and insights from your data using Google's Gemini AI.
- **Cross-filtering:** Drill down into your data with interactive filters that apply across charts.
- **Configurable:** Easily configure the application using environment variables.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/InsightDash.git
    cd InsightDash
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Set the required environment variables. Create a `.env` file in the root directory of the project and add the following:

    ```
    GOOGLE_API_KEY="your_google_api_key"
    DB_SERVER="your_db_server"
    DB_DATABASE="your_db_name"
    DB_USERNAME="your_db_username"
    DB_PASSWORD="your_db_password"
    ```

2.  Run the application:
    ```bash
    python app.py
    ```
3.  Open your web browser and navigate to `http://127.0.0.1:8050/`.

## Configuration

The application is configured using environment variables. The following variables are available:

-   `GOOGLE_API_KEY`: Your Google API key for Gemini AI.
-   `GENAI_MODEL_NAME`: The name of the generative AI model to use (defaults to `gemini-1.0-pro`).
-   `DB_SERVER`: The database server hostname or IP address.
-   `DB_DATABASE`: The name of the database.
-   `DB_USERNAME`: The username for database authentication.
-   `DB_PASSWORD`: The password for database authentication.
-   `ODBC_DRIVER`: The ODBC driver for your database (defaults to `ODBC Driver 17 for SQL Server`).
