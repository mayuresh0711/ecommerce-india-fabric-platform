import os

import pyodbc
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    server = os.getenv("DB_SERVER")
    port = os.getenv("DB_PORT", "1433")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    required_variables = {
        "DB_SERVER": server,
        "DB_PORT": port,
        "DB_NAME": database,
        "DB_USER": username,
        "DB_PASSWORD": password,
    }

    missing_variables = [
        name
        for name, value in required_variables.items()
        if not value
    ]

    if missing_variables:
        raise ValueError(
            "Missing database environment variables: "
            + ", ".join(missing_variables)
        )

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)