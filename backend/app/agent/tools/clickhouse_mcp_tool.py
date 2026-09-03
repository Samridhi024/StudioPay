import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def create_mcp_environment() -> dict[str, str]:
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
        "CLICKHOUSE_ALLOW_WRITE_ACCESS": "false",
        "CLICKHOUSE_ALLOW_DROP": "false",
    }


def extract_tool_text(result) -> str:
    if result.isError:
        raise RuntimeError(
            "ClickHouse MCP query failed"
        )

    text_blocks = []

    for content_block in result.content:
        block_text = getattr(
            content_block,
            "text",
            None,
        )

        if block_text:
            text_blocks.append(block_text)

    return "\n".join(text_blocks)


async def get_agent_payment_context() -> dict[str, str]:
    """
    Retrieve effective payment states through the official
    read-only mcp-clickhouse server.
    """

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "mcp_clickhouse.main",
        ],
        env=create_mcp_environment(),
    )

    async with stdio_client(
        server_parameters
    ) as (read_stream, write_stream):

        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:

            await session.initialize()

            summary_result = await session.call_tool(
                "run_query",
                arguments={
                    "query": """
                        WITH payment_states AS
                        (
                            SELECT
                                p.payment_id,
                                toFloat64(p.amount)
                                    AS amount,
                                if(
                                    r.recovered_count > 0,
                                    'recovered',
                                    toString(p.status)
                                ) AS effective_status
                            FROM studiopay.payments AS p
                            LEFT JOIN
                            (
                                SELECT
                                    payment_id,
                                    count()
                                        AS recovered_count
                                FROM
                                    studiopay.recovery_attempts
                                WHERE result = 'recovered'
                                GROUP BY payment_id
                            ) AS r
                                ON p.payment_id =
                                   r.payment_id
                        )
                        SELECT
                            count() AS total_payments,
                            countIf(
                                effective_status = 'paid'
                            ) AS paid_payments,
                            countIf(
                                effective_status = 'failed'
                            ) AS failed_payments,
                            countIf(
                                effective_status = 'recovered'
                            ) AS recovered_payments,
                            countIf(
                                effective_status = 'pending'
                            ) AS pending_payments,
                            toFloat64(
                                sumIf(
                                    amount,
                                    effective_status = 'failed'
                                )
                            ) AS revenue_at_risk,
                            toFloat64(
                                sumIf(
                                    amount,
                                    effective_status = 'recovered'
                                )
                            ) AS recovered_revenue
                        FROM payment_states
                    """,
                },
            )

            payments_result = await session.call_tool(
                "run_query",
                arguments={
                    "query": """
                        SELECT
                            p.invoice_id,
                            p.customer_name,
                            toFloat64(p.amount) AS amount,
                            p.currency,

                            if(
                                r.recovered_count > 0,
                                'recovered',
                                toString(p.status)
                            ) AS effective_status,

                            p.failure_code,
                            p.failure_reason,
                            p.attempt_count

                        FROM studiopay.payments AS p

                        LEFT JOIN
                        (
                            SELECT
                                payment_id,
                                count()
                                    AS recovered_count
                            FROM
                                studiopay.recovery_attempts
                            WHERE result = 'recovered'
                            GROUP BY payment_id
                        ) AS r
                            ON p.payment_id =
                               r.payment_id

                        ORDER BY p.payment_date DESC
                        LIMIT 20
                    """,
                },
            )

            return {
                "summary": extract_tool_text(
                    summary_result
                ),
                "payments": extract_tool_text(
                    payments_result
                ),
            }