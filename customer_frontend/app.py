import os
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(
    PROJECT_ROOT / ".env"
)

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
).rstrip("/")

IST = timezone(
    timedelta(hours=5, minutes=30)
)


st.set_page_config(
    page_title="StudioPay Customer",
    page_icon="💳",
    layout="centered",
)


def format_currency(
    amount: float,
    currency: str = "INR",
) -> str:
    if currency == "INR":
        return f"₹{amount:,.2f}"

    return f"{currency} {amount:,.2f}"


def format_datetime_ist(
    value,
) -> str:
    if not value:
        return "-"

    if isinstance(value, datetime):
        parsed_datetime = value
    else:
        parsed_datetime = datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )

    if parsed_datetime.tzinfo is None:
        parsed_datetime = (
            parsed_datetime.replace(
                tzinfo=timezone.utc
            )
        )

    return (
        parsed_datetime
        .astimezone(IST)
        .strftime(
            "%d %b %Y, %I:%M %p IST"
        )
    )


def get_error_message(
    error: requests.RequestException,
) -> str:
    response = getattr(
        error,
        "response",
        None,
    )

    if response is not None:
        try:
            response_data = response.json()

            if response_data.get("detail"):
                return str(
                    response_data["detail"]
                )

        except ValueError:
            pass

    return str(error)


def fetch_payment_status(
    invoice_id: str,
    customer_email: str,
    customer_phone: str,
) -> dict:
    response = requests.post(
        (
            f"{BACKEND_URL}/api/customer/"
            "payment-status"
        ),
        json={
            "invoice_id": invoice_id,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
        },
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


st.title("StudioPay")
st.caption("Customer Payment Portal")

st.info(
    "Enter the details associated with your invoice "
    "to check its payment and recovery status."
)


with st.form(
    "customer-payment-search"
):
    invoice_id = st.text_input(
        "Invoice ID",
        placeholder="INV-2041",
    )

    customer_email = st.text_input(
        "Email address",
        placeholder="customer@example.com",
    )

    customer_phone = st.text_input(
        "Phone number with country code",
        placeholder="+919876543210",
    )

    submitted = st.form_submit_button(
        "Check payment status",
        use_container_width=True,
        type="primary",
    )


if submitted:
    if not invoice_id.strip():
        st.error("Enter your invoice ID.")

    elif not customer_email.strip():
        st.error("Enter your email address.")

    elif not customer_phone.strip():
        st.error("Enter your phone number.")

    else:
        with st.spinner(
            "Checking payment status..."
        ):
            try:
                payment_result = (
                    fetch_payment_status(
                        invoice_id=invoice_id.strip(),
                        customer_email=(
                            customer_email.strip()
                        ),
                        customer_phone=(
                            customer_phone.strip()
                        ),
                    )
                )

                st.session_state[
                    "customer_payment_result"
                ] = payment_result

            except requests.RequestException as error:
                st.session_state.pop(
                    "customer_payment_result",
                    None,
                )

                st.error(
                    get_error_message(error)
                )


payment_result = st.session_state.get(
    "customer_payment_result"
)

if payment_result:
    st.divider()

    payment = payment_result["payment"]
    recovery = payment_result["recovery"]

    st.subheader(
        f'Invoice {payment["invoice_id"]}'
    )

    detail_columns = st.columns(2)

    detail_columns[0].metric(
        "Amount",
        format_currency(
            payment["amount"],
            payment["currency"],
        ),
    )

    detail_columns[1].metric(
        "Status",
        payment["status"].title(),
    )

    st.write(
        f'**Customer:** {payment["customer_name"]}'
    )

    st.write(
        f'**Business:** {payment["vendor_name"]}'
    )

    status = payment["status"]

    if status == "recovered":
        st.success(
            "Payment completed successfully. "
            "No further action is required."
        )

    elif status == "paid":
        st.success(
            "This invoice has already been paid."
        )

    elif status == "pending":
        st.info(
            "Your payment is currently pending. "
            "Please wait while it is confirmed."
        )

    elif status == "failed":
        st.error(
            "The previous payment attempt was not "
            "successful."
        )

        if payment.get("failure_reason"):
            st.write(
                "**Reason:** "
                f'{payment["failure_reason"]}'
            )

        action = recovery["action"]

        payment_link = recovery.get(
            "payment_link"
        )

        smart_retry = recovery.get(
            "smart_retry"
        )

        manual_review = recovery.get(
            "manual_review"
        )

        if (
            action == "send_payment_link"
            and payment_link
            and payment_link.get("short_url")
        ):
            st.warning(
                "A secure recovery payment link is "
                "available."
            )

            st.link_button(
                "Pay securely with Razorpay",
                payment_link["short_url"],
                use_container_width=True,
                type="primary",
            )

        elif action == "send_payment_link":
            st.info(
                "Your recovery link is being prepared. "
                "Please check again shortly."
            )

        elif (
            action == "smart_retry"
            and smart_retry
        ):
            st.info(
                "A payment recovery follow-up has "
                "been scheduled."
            )

            st.write(
                "**Scheduled time:** "
                f'{format_datetime_ist(
                    smart_retry.get("next_action_at")
                )}'
            )

        elif action == "smart_retry":
            retry_minutes = recovery.get(
                "retry_after_minutes"
            )

            st.info(
                "This payment is eligible for a "
                "recovery retry."
            )

            if retry_minutes:
                st.write(
                    "**Recommended delay:** "
                    f"{retry_minutes} minutes"
                )

        elif action == "manual_review":
            if (
                manual_review
                and manual_review["result"]
                == "approved"
            ):
                st.info(
                    "Your payment recovery has been "
                    "approved for manual follow-up."
                )

            elif (
                manual_review
                and manual_review["result"]
                == "rejected"
            ):
                st.warning(
                    "The manual recovery request was "
                    "not approved. Please contact the "
                    "business for assistance."
                )

            else:
                st.warning(
                    "This payment is being reviewed by "
                    "the business. No action is required "
                    "from you right now."
                )

        else:
            st.info(recovery["reason"])


st.divider()

st.caption(
    "For your privacy, StudioPay only displays a "
    "payment when the invoice, email and phone number "
    "match."
)