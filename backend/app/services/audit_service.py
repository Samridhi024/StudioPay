import json

from app.db.clickhouse import get_clickhouse_client


def get_recent_audit_events(
    limit: int = 50,
) -> list[dict]:
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(a.event_id) AS event_id,
            ifNull(
                toString(a.payment_id),
                ''
            ) AS payment_id,
            ifNull(p.invoice_id, '') AS invoice_id,
            a.event_type,
            a.actor,
            a.decision,
            a.metadata,
            a.created_at

        FROM studiopay.audit_logs AS a

        LEFT JOIN studiopay.payments AS p
            ON a.payment_id = p.payment_id

        ORDER BY a.created_at DESC
        LIMIT {limit:UInt32}
        """,
        parameters={
            "limit": limit,
        },
    )

    audit_events = []

    for row in result.result_rows:
        event = dict(
            zip(result.column_names, row)
        )

        try:
            event["metadata"] = json.loads(
                event["metadata"]
            )
        except (
            TypeError,
            json.JSONDecodeError,
        ):
            event["metadata"] = {}

        audit_events.append(event)

    return audit_events