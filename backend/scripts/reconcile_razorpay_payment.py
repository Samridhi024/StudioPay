import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))


from app.agent.tools.razorpay_tool import (  # noqa: E402
    get_razorpay_client,
)
from app.services.webhook_service import (  # noqa: E402
    handle_payment_link_paid,
)


def reconcile_payment(
    link_id: str,
    payment_id: str,
):
    if not link_id.startswith("plink_"):
        raise ValueError(
            "Payment Link ID must start with plink_"
        )

    if not payment_id.startswith("pay_"):
        raise ValueError(
            "Payment ID must start with pay_"
        )

    print("Using link ID:", link_id)
    print("Using payment ID:", payment_id)

    client = get_razorpay_client()

    payment_link = client.payment_link.fetch(
        link_id
    )

    razorpay_payment = client.payment.fetch(
        payment_id
    )

    print(
        "Payment-link reference:",
        payment_link.get("reference_id"),
    )

    print(
        "StudioPay payment ID:",
        (payment_link.get("notes") or {}).get(
            "studiopay_payment_id"
        ),
    )

    print(
        "Payment-link status:",
        payment_link.get("status"),
    )

    print(
        "Payment status:",
        razorpay_payment.get("status"),
    )

    if payment_link.get("status") != "paid":
        raise RuntimeError(
            "Razorpay payment link is not paid"
        )

    if razorpay_payment.get("status") != "captured":
        raise RuntimeError(
            "Razorpay payment is not captured"
        )

    webhook_payload = {
        "payload": {
            "payment_link": {
                "entity": payment_link,
            },
            "payment": {
                "entity": razorpay_payment,
            },
        }
    }

    result = handle_payment_link_paid(
        webhook_payload
    )

    print("Reconciliation successful")
    print(result)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile an existing Razorpay Test payment"
        )
    )

    parser.add_argument(
        "--link-id",
        required=True,
        help=(
            "Razorpay Payment Link ID beginning "
            "with plink_"
        ),
    )

    parser.add_argument(
        "--payment-id",
        required=True,
        help=(
            "Razorpay Payment ID beginning "
            "with pay_"
        ),
    )

    arguments = parser.parse_args()

    reconcile_payment(
        link_id=arguments.link_id,
        payment_id=arguments.payment_id,
    )


if __name__ == "__main__":
    main()