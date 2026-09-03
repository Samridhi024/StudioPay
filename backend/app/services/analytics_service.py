from app.db.clickhouse import get_clickhouse_client


def get_dashboard_summary():
    client = get_clickhouse_client()

    result = client.query(
        """
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
            ) AS recovered_revenue,
            ifNull(
                round(
                    100.0 *
                    countIf(
                        effective_status = 'recovered'
                    ) /
                    nullIf(
                        countIf(
                            effective_status IN (
                                'failed',
                                'recovered'
                            )
                        ),
                        0
                    ),
                    2
                ),
                0
            ) AS recovery_rate
        FROM
        (
            SELECT
                p.amount,
                if(
                    p.status = 'recovered'
                    OR coalesce(
                        recovery_state.recovered,
                        0
                    ) = 1,
                    'recovered',
                    p.status
                ) AS effective_status
            FROM studiopay.payments AS p
            LEFT JOIN
            (
                SELECT
                    payment_id,
                    toUInt8(1) AS recovered,
                    max(attempted_at) AS recovered_at
                FROM studiopay.recovery_attempts
                WHERE result = 'recovered'
                GROUP BY payment_id
            ) AS recovery_state
                ON p.payment_id =
                    recovery_state.payment_id
        )
        """
    )

    return dict(
        zip(
            result.column_names,
            result.result_rows[0],
        )
    )


def get_recent_payments(
    limit: int = 10,
):
    client = get_clickhouse_client()

    result = client.query(
        """
        SELECT
            toString(p.payment_id) AS payment_id,
            p.invoice_id,
            v.name AS vendor_name,
            p.customer_name,
            p.customer_email,
            p.customer_phone,
            toFloat64(p.amount) AS amount,
            p.currency,
            if(
                p.status = 'recovered'
                OR coalesce(
                    recovery_state.recovered,
                    0
                ) = 1,
                'recovered',
                p.status
            ) AS status,
            p.failure_code,
            p.failure_reason,
            p.attempt_count,
            p.payment_date,
            p.next_retry_at,
            if(
                coalesce(
                    recovery_state.recovered,
                    0
                ) = 1,
                toNullable(
                    recovery_state.recovered_at
                ),
                p.recovered_at
            ) AS recovered_at
        FROM studiopay.payments AS p
        LEFT JOIN studiopay.vendors AS v
            ON p.vendor_id = v.vendor_id
        LEFT JOIN
        (
            SELECT
                payment_id,
                toUInt8(1) AS recovered,
                max(attempted_at) AS recovered_at
            FROM studiopay.recovery_attempts
            WHERE result = 'recovered'
            GROUP BY payment_id
        ) AS recovery_state
            ON p.payment_id =
                recovery_state.payment_id
        ORDER BY p.payment_date DESC
        LIMIT {limit:UInt32}
        """,
        parameters={
            "limit": limit,
        },
    )

    return [
        dict(zip(result.column_names, row))
        for row in result.result_rows
    ]