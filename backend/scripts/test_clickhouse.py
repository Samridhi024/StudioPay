import os
from pathlib import Path

import clickhouse_connect
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def test_connection():
    client = clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        # database="default",
        database=os.getenv("CLICKHOUSE_DATABASE", "default"),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )

    result = client.query(
        "SELECT version() AS version, currentDatabase() AS database"
    )

    version, database = result.result_rows[0]

    print("ClickHouse connection successful")
    print(f"Version: {version}")
    print(f"Database: {database}")


if __name__ == "__main__":
    test_connection()