import hashlib
import hmac
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

WEBHOOK_URL = (
    "http://localhost:8000/api/webhooks/razorpay"
)


def create_signature(
    body: bytes,
    secret: str,
) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()


def test_webhook():
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    if not secret:
        raise RuntimeError(
            "RAZORPAY_WEBHOOK_SECRET is missing"
        )

    payload = {
        "event": "studiopay.webhook.test",
        "payload": {},
    }

    body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = create_signature(
        body,
        secret,
    )

    response = requests.post(
        WEBHOOK_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
        timeout=10,
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")

    response.raise_for_status()


if __name__ == "__main__":
    test_webhook()