CREATE DATABASE IF NOT EXISTS studiopay;

CREATE TABLE IF NOT EXISTS studiopay.vendors
(
    vendor_id UUID DEFAULT generateUUIDv4(),
    name String,
    email String,
    category LowCardinality(String),
    risk_level LowCardinality(String) DEFAULT 'low',
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY vendor_id;

CREATE TABLE IF NOT EXISTS studiopay.payments
(
    payment_id UUID DEFAULT generateUUIDv4(),
    vendor_id UUID,
    invoice_id String,
    razorpay_payment_id String DEFAULT '',
    customer_name String,
    customer_email String,
    customer_phone String DEFAULT '',
    amount Decimal(14, 2),
    currency FixedString(3) DEFAULT 'INR',
    status LowCardinality(String),
    failure_code String DEFAULT '',
    failure_reason String DEFAULT '',
    attempt_count UInt8 DEFAULT 0,
    payment_date DateTime64(3, 'UTC'),
    next_retry_at Nullable(DateTime64(3, 'UTC')),
    recovered_at Nullable(DateTime64(3, 'UTC')),
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(payment_date)
ORDER BY (status, payment_date, payment_id);

CREATE TABLE IF NOT EXISTS studiopay.recovery_attempts
(
    attempt_id UUID DEFAULT generateUUIDv4(),
    payment_id UUID,
    action LowCardinality(String),
    channel LowCardinality(String),
    result LowCardinality(String),
    amount_recovered Decimal(14, 2) DEFAULT 0,
    failure_reason String DEFAULT '',
    initiated_by LowCardinality(String),
    attempted_at DateTime64(3, 'UTC') DEFAULT now64(3),
    next_action_at Nullable(DateTime64(3, 'UTC'))
)
ENGINE = MergeTree
ORDER BY (payment_id, attempted_at, attempt_id);

CREATE TABLE IF NOT EXISTS studiopay.audit_logs
(
    event_id UUID DEFAULT generateUUIDv4(),
    payment_id Nullable(UUID),
    event_type LowCardinality(String),
    actor LowCardinality(String),
    decision String,
    metadata String DEFAULT '{}',
    created_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY (created_at, event_id);