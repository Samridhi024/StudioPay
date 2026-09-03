import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def create_mcp_environment():
    """
    Pass the current environment and ClickHouse configuration
    to the MCP server subprocess.
    """

    return {
        **os.environ,
        "CLICKHOUSE_HOST": os.getenv(
            "CLICKHOUSE_HOST",
            "",
        ),
        "CLICKHOUSE_PORT": os.getenv(
            "CLICKHOUSE_PORT",
            "8443",
        ),
        "CLICKHOUSE_USER": os.getenv(
            "CLICKHOUSE_USER",
            "default",
        ),
        "CLICKHOUSE_PASSWORD": os.getenv(
            "CLICKHOUSE_PASSWORD",
            "",
        ),
        "CLICKHOUSE_DATABASE": os.getenv(
            "CLICKHOUSE_DATABASE",
            "studiopay",
        ),
        "CLICKHOUSE_SECURE": os.getenv(
            "CLICKHOUSE_SECURE",
            "true",
        ),
        "CLICKHOUSE_VERIFY": "true",

        # Keep MCP read-only for safety.
        "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
        "CLICKHOUSE_ALLOW_DROP": "false",
    }


def print_tool_result(result):
    for content_block in result.content:
        text = getattr(content_block, "text", None)

        if text:
            print(text)


async def test_mcp():
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "mcp_clickhouse.main",
        ],
        env=create_mcp_environment(),
    )

    print("Starting official mcp-clickhouse server...")

    async with stdio_client(
        server_parameters
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            print("\nMCP connection initialized")

            tools_result = await session.list_tools()
            tool_names = [
                tool.name
                for tool in tools_result.tools
            ]

            print("\nAvailable MCP tools:")

            for tool_name in tool_names:
                print(f"- {tool_name}")

            required_tools = {
                "list_databases",
                "list_tables",
                "run_query",
            }

            missing_tools = required_tools.difference(
                tool_names
            )

            if missing_tools:
                raise RuntimeError(
                    "Missing required MCP tools: "
                    + ", ".join(sorted(missing_tools))
                )

            print("\nTables returned through MCP:")

            tables_result = await session.call_tool(
                "list_tables",
                arguments={
                    "database": "studiopay",
                    "include_detailed_columns": False,
                },
            )

            print_tool_result(tables_result)

            print("\nDashboard metrics returned through MCP:")

            metrics_result = await session.call_tool(
                "run_query",
                arguments={
                    "query": """
                        SELECT
                            count() AS total_payments,
                            countIf(status = 'failed')
                                AS failed_payments,
                            toFloat64(
                                sumIf(
                                    amount,
                                    status = 'failed'
                                )
                            ) AS revenue_at_risk,
                            toFloat64(
                                sumIf(
                                    amount,
                                    status = 'recovered'
                                )
                            ) AS recovered_revenue
                        FROM studiopay.payments
                    """,
                },
            )

            print_tool_result(metrics_result)

            if metrics_result.isError:
                raise RuntimeError(
                    "ClickHouse MCP query failed"
                )

            print(
                "\nOfficial ClickHouse MCP "
                "runtime verification successful"
            )


if __name__ == "__main__":
    asyncio.run(test_mcp())