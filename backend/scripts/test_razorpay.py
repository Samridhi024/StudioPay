import os
from pathlib import Path

import razorpay
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def test_razorpay_connection():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET "
            "is missing from .env"
        )

    # Prevent accidental use of Live Mode credentials.
    if not key_id.startswith("rzp_test_"):
        raise RuntimeError(
            "StudioPay must use a Razorpay Test Mode key"
        )

    client = razorpay.Client(
        auth=(key_id, key_secret)
    )

    # Read-only request; it does not create or charge anything.
    orders = client.order.all(
        {
            "count": 1,
        }
    )

    masked_key = f"{key_id[:12]}...{key_id[-4:]}"

    print("Razorpay Test Mode connection successful")
    print(f"Key ID: {masked_key}")
    print(f"Existing test orders: {orders.get('count', 0)}")


if __name__ == "__main__":
    test_razorpay_connection()