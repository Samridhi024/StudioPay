import os
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = Path(__file__).resolve().parent / "create_tables.sql"

load_dotenv(PROJECT_ROOT / ".env", override=True)


def create_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database="default",
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )


def setup_database():
    client = create_client()

    sql_content = SQL_FILE.read_text(encoding="utf-8")

    statements = [
        statement.strip()
        for statement in sql_content.split(";")
        if statement.strip()
    ]

    for statement in statements:
        client.command(statement)

    tables = client.query(
        """
        SELECT name
        FROM system.tables
        WHERE database = 'studiopay'
        ORDER BY name
        """
    )

    print("StudioPay database created successfully")
    print("Tables:")

    for row in tables.result_rows:
        print(f"- {row[0]}")


if __name__ == "__main__":
    setup_database()