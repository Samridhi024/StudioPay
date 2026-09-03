import html
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000",
).rstrip("/")


st.set_page_config(
    page_title="StudioPay Admin",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Visual design
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        :root {
            --sp-bg: #07111f;
            --sp-surface: rgba(15, 28, 48, 0.86);
            --sp-surface-2: rgba(20, 38, 64, 0.92);
            --sp-border: rgba(148, 163, 184, 0.18);
            --sp-text: #f8fafc;
            --sp-muted: #94a3b8;
            --sp-blue: #38bdf8;
            --sp-indigo: #818cf8;
            --sp-green: #34d399;
            --sp-orange: #fb923c;
            --sp-red: #fb7185;
        }

        .stApp {
            background:
                radial-gradient(circle at 85% 5%, rgba(56, 189, 248, 0.12), transparent 28%),
                radial-gradient(circle at 20% 20%, rgba(129, 140, 248, 0.10), transparent 25%),
                var(--sp-bg);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0c1728 0%, #0a1322 100%);
            border-right: 1px solid var(--sp-border);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #cbd5e1;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.8rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            color: var(--sp-text);
            letter-spacing: -0.025em;
        }

        .sp-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin: 0.25rem 0 1.25rem 0;
        }

        .sp-brand-mark {
            width: 2.65rem;
            height: 2.65rem;
            display: grid;
            place-items: center;
            border-radius: 0.85rem;
            color: white;
            font-size: 1.25rem;
            background: linear-gradient(135deg, #2563eb, #06b6d4);
            box-shadow: 0 12px 30px rgba(14, 165, 233, 0.22);
        }

        .sp-brand-title {
            color: #f8fafc;
            font-size: 1.2rem;
            font-weight: 750;
            line-height: 1.1;
        }

        .sp-brand-subtitle {
            color: #94a3b8;
            font-size: 0.72rem;
            margin-top: 0.2rem;
        }

        .sp-hero {
            position: relative;
            overflow: hidden;
            padding: 1.6rem 1.7rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(125, 211, 252, 0.18);
            border-radius: 1.3rem;
            background: linear-gradient(120deg, rgba(30, 64, 175, 0.35), rgba(8, 47, 73, 0.46));
            box-shadow: 0 18px 55px rgba(2, 8, 23, 0.25);
        }

        .sp-hero::after {
            content: "";
            position: absolute;
            right: -4rem;
            top: -5rem;
            width: 15rem;
            height: 15rem;
            border-radius: 50%;
            background: rgba(56, 189, 248, 0.12);
            filter: blur(4px);
        }

        .sp-eyebrow {
            color: #7dd3fc;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 700;
        }

        .sp-hero-title {
            color: #f8fafc;
            font-size: clamp(1.7rem, 3vw, 2.45rem);
            font-weight: 800;
            letter-spacing: -0.04em;
            margin: 0.35rem 0 0.3rem 0;
        }

        .sp-hero-copy {
            color: #cbd5e1;
            max-width: 760px;
            line-height: 1.6;
            font-size: 0.92rem;
        }

        .sp-metric {
            min-height: 128px;
            padding: 1.05rem 1.1rem;
            border: 1px solid var(--sp-border);
            border-radius: 1rem;
            background: linear-gradient(145deg, rgba(20, 38, 64, 0.92), rgba(11, 24, 42, 0.92));
            box-shadow: 0 12px 28px rgba(2, 8, 23, 0.20);
        }

        .sp-metric-label {
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .sp-metric-value {
            color: #f8fafc;
            font-size: clamp(1.45rem, 2.5vw, 2rem);
            font-weight: 790;
            letter-spacing: -0.04em;
            margin-top: 0.55rem;
        }

        .sp-metric-note {
            color: #64748b;
            font-size: 0.74rem;
            margin-top: 0.35rem;
        }

        .sp-section-title {
            color: #f8fafc;
            font-size: 1.35rem;
            font-weight: 760;
            letter-spacing: -0.025em;
            margin-bottom: 0.15rem;
        }

        .sp-section-copy {
            color: #94a3b8;
            font-size: 0.86rem;
            margin-bottom: 1rem;
        }

        .sp-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 0.7rem;
            margin-bottom: 0.45rem;
            border: 1px solid var(--sp-border);
            border-radius: 0.7rem;
            background: rgba(15, 28, 48, 0.74);
            color: #cbd5e1;
            font-size: 0.79rem;
        }

        .sp-dot {
            width: 0.52rem;
            height: 0.52rem;
            border-radius: 50%;
            display: inline-block;
            margin-right: 0.45rem;
        }

        .sp-dot-ok {
            background: #34d399;
            box-shadow: 0 0 10px rgba(52, 211, 153, 0.7);
        }

        .sp-dot-bad {
            background: #fb7185;
            box-shadow: 0 0 10px rgba(251, 113, 133, 0.7);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--sp-border);
            border-radius: 0.9rem;
            overflow: hidden;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--sp-border);
            border-radius: 0.9rem;
            background: rgba(10, 22, 38, 0.64);
            overflow: hidden;
        }

        div[data-testid="stForm"] {
            border: 1px solid var(--sp-border);
            border-radius: 1rem;
            background: rgba(10, 22, 38, 0.66);
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 2.65rem;
            border-radius: 0.72rem;
            border: 1px solid rgba(125, 211, 252, 0.28);
            transition: transform 120ms ease, border-color 120ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(125, 211, 252, 0.72);
        }

        .sp-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            background: rgba(56, 189, 248, 0.12);
            color: #7dd3fc;
            border: 1px solid rgba(56, 189, 248, 0.18);
        }

        [data-testid="stChatMessage"] {
            border: 1px solid var(--sp-border);
            border-radius: 0.9rem;
            background: rgba(10, 22, 38, 0.58);
            padding: 0.35rem 0.55rem;
            margin-bottom: 0.55rem;
        }

        div[data-testid="stNotification"] {
            border-radius: 0.85rem;
        }

        hr {
            border-color: var(--sp-border) !important;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            .sp-hero {
                padding: 1.2rem;
            }

            .sp-metric {
                min-height: 108px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Backend API functions
# ---------------------------------------------------------

@st.cache_data(ttl=15, show_spinner=False)
def fetch_summary():
    response = requests.get(
        f"{BACKEND_URL}/api/dashboard/summary",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=15, show_spinner=False)
def fetch_payments():
    response = requests.get(
        f"{BACKEND_URL}/api/dashboard/payments",
        params={"limit": 100},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["payments"]


@st.cache_data(ttl=15, show_spinner=False)
def fetch_recommendations():
    response = requests.get(
        f"{BACKEND_URL}/api/policy/recommendations",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["recommendations"]


@st.cache_data(ttl=15, show_spinner=False)
def fetch_audit_events():
    response = requests.get(
        f"{BACKEND_URL}/api/audit/recent",
        params={"limit": 50},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["events"]


@st.cache_data(ttl=10, show_spinner=False)
def fetch_system_status():
    health_response = requests.get(
        f"{BACKEND_URL}/api/health",
        timeout=5,
    )
    health_response.raise_for_status()

    status = {
        "backend": True,
        "clickhouse": True,
        "razorpay": False,
        "huggingface": False,
    }

    try:
        integration_response = requests.get(
            f"{BACKEND_URL}/api/integrations/status",
            timeout=5,
        )
        integration_response.raise_for_status()
        integrations = integration_response.json()

        status["clickhouse"] = bool(
            integrations.get("clickhouse", {}).get(
                "configured",
                True,
            )
        )
        status["razorpay"] = bool(
            integrations.get("razorpay", {}).get(
                "configured",
                False,
            )
        )
        status["huggingface"] = bool(
            integrations.get("huggingface", {}).get(
                "configured",
                False,
            )
        )
    except requests.RequestException:
        pass

    return status


def send_agent_message(message: str):
    response = requests.post(
        f"{BACKEND_URL}/api/agent/chat",
        json={"message": message},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def execute_recovery_action(
    payment_id: str,
    action: str,
):
    endpoint_by_action = {
        "send_payment_link": "payment-link",
        "smart_retry": "smart-retry",
    }

    endpoint = endpoint_by_action.get(action)

    if endpoint is None:
        raise ValueError(
            f"Unsupported recovery action: {action}"
        )

    response = requests.post(
        (
            f"{BACKEND_URL}/api/payments/"
            f"{payment_id}/{endpoint}"
        ),
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def submit_manual_review(
    payment_id: str,
    approved: bool,
    reviewer: str,
):
    response = requests.post(
        (
            f"{BACKEND_URL}/api/payments/"
            f"{payment_id}/manual-review"
        ),
        json={
            "approved": approved,
            "reviewer": reviewer,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------
# Formatting and UI helpers
# ---------------------------------------------------------

def format_currency(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def format_ist_datetime(value) -> str:
    if not value:
        return "Not scheduled"

    try:
        timestamp = pd.to_datetime(value, utc=True)
        timestamp = timestamp.tz_convert("Asia/Kolkata")
        return timestamp.strftime("%d %b %Y, %I:%M %p IST")
    except (TypeError, ValueError):
        return str(value)


def get_request_error_message(
    error: requests.RequestException,
) -> str:
    response = getattr(error, "response", None)

    if response is not None:
        try:
            response_data = response.json()

            if response_data.get("detail"):
                return str(response_data["detail"])
        except ValueError:
            pass

    return str(error)


def section_heading(title: str, description: str):
    st.markdown(
        (
            '<div class="sp-section-title">'
            f"{html.escape(title)}"
            "</div>"
            '<div class="sp-section-copy">'
            f"{html.escape(description)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def metric_card(
    label: str,
    value: str,
    note: str,
):
    st.markdown(
        (
            '<div class="sp-metric">'
            '<div class="sp-metric-label">'
            f"{html.escape(label)}"
            "</div>"
            '<div class="sp-metric-value">'
            f"{html.escape(str(value))}"
            "</div>"
            '<div class="sp-metric-note">'
            f"{html.escape(note)}"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_hero(
    eyebrow: str,
    title: str,
    description: str,
):
    st.markdown(
        (
            '<div class="sp-hero">'
            f'<div class="sp-eyebrow">{html.escape(eyebrow)}</div>'
            f'<div class="sp-hero-title">{html.escape(title)}</div>'
            f'<div class="sp-hero-copy">{html.escape(description)}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def status_row(label: str, connected: bool):
    dot_class = "sp-dot-ok" if connected else "sp-dot-bad"
    state = "Connected" if connected else "Unavailable"

    st.markdown(
        (
            '<div class="sp-status">'
            "<span>"
            f'<span class="sp-dot {dot_class}"></span>'
            f"{html.escape(label)}"
            "</span>"
            f"<span>{state}</span>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def prepare_payment_dataframe(payments: list[dict]):
    dataframe = pd.DataFrame(payments)

    if dataframe.empty:
        return dataframe

    if "customer_phone" not in dataframe.columns:
        dataframe["customer_phone"] = ""

    if "payment_date" in dataframe.columns:
        dataframe["payment_date"] = pd.to_datetime(
            dataframe["payment_date"],
            errors="coerce",
            utc=True,
        ).dt.tz_convert("Asia/Kolkata")

    return dataframe


def render_payment_table(
    payments: list[dict],
    key_prefix: str,
    default_status: str = "All",
):
    dataframe = prepare_payment_dataframe(payments)

    filter_column, search_column = st.columns([1, 2])

    with filter_column:
        selected_status = st.selectbox(
            "Payment status",
            options=[
                "All",
                "paid",
                "failed",
                "recovered",
                "pending",
            ],
            index=[
                "All",
                "paid",
                "failed",
                "recovered",
                "pending",
            ].index(default_status),
            key=f"{key_prefix}-status",
        )

    with search_column:
        search_text = st.text_input(
            "Search invoice, vendor or customer",
            placeholder="Try INV-1015 or a customer name",
            key=f"{key_prefix}-search",
        ).strip()

    if dataframe.empty:
        st.info("No payments found.")
        return

    if selected_status != "All":
        dataframe = dataframe[
            dataframe["status"] == selected_status
        ]

    if search_text:
        searchable_columns = [
            column
            for column in [
                "invoice_id",
                "vendor_name",
                "customer_name",
                "customer_email",
                "customer_phone",
            ]
            if column in dataframe.columns
        ]

        search_mask = pd.Series(
            False,
            index=dataframe.index,
        )

        for column in searchable_columns:
            search_mask |= (
                dataframe[column]
                .fillna("")
                .astype(str)
                .str.contains(
                    search_text,
                    case=False,
                    regex=False,
                )
            )

        dataframe = dataframe[search_mask]

    if dataframe.empty:
        st.info("No payments match the selected filters.")
        return

    display_columns = [
        column
        for column in [
            "invoice_id",
            "vendor_name",
            "customer_name",
            "customer_phone",
            "amount",
            "currency",
            "status",
            "failure_reason",
            "attempt_count",
            "payment_date",
        ]
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[display_columns],
        use_container_width=True,
        hide_index=True,
        height=min(540, 74 + len(dataframe) * 35),
        column_config={
            "invoice_id": "Invoice",
            "vendor_name": "Vendor",
            "customer_name": "Customer",
            "customer_phone": "Phone",
            "amount": st.column_config.NumberColumn(
                "Amount",
                format="₹ %.2f",
            ),
            "currency": "Currency",
            "status": "Status",
            "failure_reason": "Failure reason",
            "attempt_count": "Attempts",
            "payment_date": st.column_config.DatetimeColumn(
                "Payment date",
                format="DD MMM YYYY, hh:mm a",
            ),
        },
    )


ACTION_LABELS = {
    "smart_retry": "Smart retry",
    "send_payment_link": "Send payment link",
    "customer_notification": "Notify customer",
    "manual_review": "Manual review",
    "no_action": "No action",
}


def retry_delay_label(minutes) -> str:
    if minutes == 1440:
        return "24 hours"
    if minutes:
        return f"{minutes} minutes"
    return "—"


def get_recommendation_groups(recommendations):
    automatic = [
        item
        for item in recommendations
        if (
            item["decision"]["can_execute_automatically"]
            and item["decision"]["action"]
            in {"send_payment_link", "smart_retry"}
        )
    ]

    pending_reviews = [
        item
        for item in recommendations
        if (
            item["decision"]["requires_approval"]
            and not item.get("review")
        )
    ]

    reviewed = [
        item
        for item in recommendations
        if (
            item["decision"]["requires_approval"]
            and item.get("review")
        )
    ]

    return automatic, pending_reviews, reviewed


# ---------------------------------------------------------
# Page renderers
# ---------------------------------------------------------

def render_overview(summary, payments, recommendations):
    render_hero(
        "Revenue command center",
        "See what needs attention—without hunting through the page.",
        (
            "Track payment health, recovered revenue and the most urgent "
            "recovery work from one focused workspace."
        ),
    )

    metric_columns = st.columns(4)

    with metric_columns[0]:
        metric_card(
            "Revenue at risk",
            format_currency(summary["revenue_at_risk"]),
            "Value currently requiring recovery",
        )

    with metric_columns[1]:
        metric_card(
            "Recovered revenue",
            format_currency(summary["recovered_revenue"]),
            "Revenue brought back by StudioPay",
        )

    with metric_columns[2]:
        metric_card(
            "Recovery rate",
            f'{summary["recovery_rate"]:.2f}%',
            "Share of failed payments recovered",
        )

    with metric_columns[3]:
        metric_card(
            "Active recoveries",
            str(summary["failed_payments"]),
            "Failed payments awaiting an outcome",
        )

    st.write("")
    status_columns = st.columns(4)

    with status_columns[0]:
        metric_card(
            "Total payments",
            str(summary["total_payments"]),
            "All recorded payment attempts",
        )

    with status_columns[1]:
        metric_card(
            "Successful",
            str(summary["paid_payments"]),
            "Paid without recovery",
        )

    with status_columns[2]:
        metric_card(
            "Recovered",
            str(summary["recovered_payments"]),
            "Recovered after an initial failure",
        )

    with status_columns[3]:
        metric_card(
            "Pending",
            str(summary["pending_payments"]),
            "Waiting for payment confirmation",
        )

    st.write("")
    insight_column, workload_column = st.columns([1.05, 1])

    with insight_column:
        section_heading(
            "Payment mix",
            "A quick visual breakdown of the current payment portfolio.",
        )

        chart_data = pd.DataFrame(
            {
                "Status": [
                    "Paid",
                    "Recovered",
                    "Failed",
                    "Pending",
                ],
                "Payments": [
                    summary["paid_payments"],
                    summary["recovered_payments"],
                    summary["failed_payments"],
                    summary["pending_payments"],
                ],
            }
        ).set_index("Status")

        st.bar_chart(
            chart_data,
            color="#38bdf8",
            height=285,
        )

    with workload_column:
        automatic, pending_reviews, _ = (
            get_recommendation_groups(recommendations)
        )

        section_heading(
            "Recovery workload",
            "What the team and automation currently need to handle.",
        )

        workload_metrics = st.columns(2)
        with workload_metrics[0]:
            metric_card(
                "Automatic",
                str(len(automatic)),
                "Ready for policy-approved execution",
            )
        with workload_metrics[1]:
            metric_card(
                "Approvals",
                str(len(pending_reviews)),
                "Waiting for a human decision",
            )

        st.info(
            "Use **Recovery Center** to execute automatic actions, "
            "or **Manual Reviews** to approve high-value cases."
        )

    st.divider()
    section_heading(
        "Payment overview",
        "Filter or search the latest payment records.",
    )
    render_payment_table(
        payments,
        key_prefix="overview-payments",
    )


def render_recovery_center(recommendations):
    render_hero(
        "Policy-driven operations",
        "Recovery Center",
        (
            "Review every failed payment, understand the policy decision "
            "and run approved actions from one place."
        ),
    )

    automatic, pending_reviews, _ = get_recommendation_groups(
        recommendations
    )

    queue_columns = st.columns(3)
    with queue_columns[0]:
        metric_card(
            "Failed payments",
            str(len(recommendations)),
            "Payments currently in the recovery queue",
        )
    with queue_columns[1]:
        metric_card(
            "Automatic actions",
            str(len(automatic)),
            "Approved by policy for automatic execution",
        )
    with queue_columns[2]:
        metric_card(
            "Awaiting approval",
            str(len(pending_reviews)),
            "Cases requiring a human reviewer",
        )

    st.write("")
    queue_tab, actions_tab = st.tabs(
        ["Queue overview", "Execute actions"]
    )

    with queue_tab:
        section_heading(
            "Recommended actions",
            "Policy decisions for all currently failed payments.",
        )

        recommendation_rows = []

        for item in recommendations:
            decision = item["decision"]
            recommendation_rows.append(
                {
                    "Invoice": item["invoice_id"],
                    "Customer": item["customer_name"],
                    "Amount": item["amount"],
                    "Failure": item["failure_reason"],
                    "Recommended action": ACTION_LABELS.get(
                        decision["action"],
                        decision["action"],
                    ),
                    "Retry delay": retry_delay_label(
                        decision.get("retry_after_minutes")
                    ),
                    "Approval required": decision[
                        "requires_approval"
                    ],
                }
            )

        recommendation_dataframe = pd.DataFrame(
            recommendation_rows
        )

        if recommendation_dataframe.empty:
            st.success("There are no failed payments to recover.")
        else:
            st.dataframe(
                recommendation_dataframe,
                use_container_width=True,
                hide_index=True,
                height=min(
                    520,
                    74 + len(recommendation_dataframe) * 35,
                ),
                column_config={
                    "Amount": st.column_config.NumberColumn(
                        "Amount",
                        format="₹ %.2f",
                    ),
                    "Approval required": (
                        st.column_config.CheckboxColumn(
                            "Approval required"
                        )
                    ),
                },
            )

    with actions_tab:
        section_heading(
            "Automatic recovery actions",
            "Execute only the actions already permitted by policy.",
        )

        if "recovery_action_results" not in st.session_state:
            st.session_state.recovery_action_results = {}

        if not automatic:
            st.info(
                "No automatic recovery actions are currently available."
            )

        for item in automatic:
            decision = item["decision"]
            payment_id = item["payment_id"]
            action = decision["action"]
            action_name = ACTION_LABELS.get(action, action)

            expander_title = (
                f'{item["invoice_id"]}  ·  '
                f'{item["customer_name"]}  ·  '
                f'{format_currency(item["amount"])}'
            )

            with st.expander(expander_title):
                detail_columns = st.columns(3)
                detail_columns[0].markdown(
                    f"**Action**  \n{action_name}"
                )
                detail_columns[1].markdown(
                    f'**Attempts**  \n{item["attempt_count"]}'
                )
                detail_columns[2].markdown(
                    "**Retry delay**  \n"
                    + retry_delay_label(
                        decision.get("retry_after_minutes")
                    )
                )

                st.markdown(
                    f'**Failure:** {item["failure_reason"]}'
                )
                st.caption(
                    f'Policy explanation: {decision["reason"]}'
                )

                button_label = (
                    "Create secure payment link"
                    if action == "send_payment_link"
                    else "Schedule smart retry"
                )

                if st.button(
                    button_label,
                    key=f"recovery-action-{payment_id}",
                    use_container_width=True,
                    type="primary",
                ):
                    with st.spinner("Executing recovery action..."):
                        try:
                            action_result = execute_recovery_action(
                                payment_id=payment_id,
                                action=action,
                            )
                            st.session_state[
                                "recovery_action_results"
                            ][payment_id] = action_result
                            st.cache_data.clear()
                        except requests.RequestException as error:
                            st.error(
                                "Recovery action failed: "
                                + get_request_error_message(error)
                            )
                        except ValueError as error:
                            st.error(str(error))

                saved_result = st.session_state[
                    "recovery_action_results"
                ].get(payment_id)

                if not saved_result:
                    continue

                if action == "send_payment_link":
                    payment_link = saved_result["payment_link"]

                    if payment_link.get("reused"):
                        st.info("Existing payment link retrieved.")
                    else:
                        st.success("Payment link created successfully.")

                    link_column, notify_column = st.columns([1.3, 1])
                    with link_column:
                        st.link_button(
                            "Open Razorpay payment page",
                            payment_link["short_url"],
                            use_container_width=True,
                        )
                    with notify_column:
                        email_requested = payment_link.get(
                            "email_notification_requested",
                            False,
                        )
                        sms_requested = payment_link.get(
                            "sms_notification_requested",
                            False,
                        )
                        st.caption(
                            "Notifications requested — "
                            f"Email: {'Yes' if email_requested else 'No'} · "
                            f"SMS: {'Yes' if sms_requested else 'No'}"
                        )

                    st.caption(
                        "Razorpay Test Mode — no real payment is processed."
                    )

                elif action == "smart_retry":
                    retry = saved_result["retry"]

                    if retry.get("reused"):
                        st.info("An active retry was already scheduled.")
                    else:
                        st.success("Smart retry scheduled successfully.")

                    st.markdown(
                        "**Next action:** "
                        + format_ist_datetime(
                            retry.get("next_action_at")
                        )
                    )


def render_manual_reviews(recommendations):
    render_hero(
        "Human-in-the-loop control",
        "Manual Reviews",
        (
            "Approve or reject high-value recovery cases while keeping "
            "every decision attributable and auditable."
        ),
    )

    _, pending_reviews, reviewed = get_recommendation_groups(
        recommendations
    )

    metric_columns = st.columns(3)
    with metric_columns[0]:
        metric_card(
            "Pending reviews",
            str(len(pending_reviews)),
            "Cases that still need a reviewer",
        )
    with metric_columns[1]:
        approved_count = sum(
            1
            for item in reviewed
            if item["review"]["result"] == "approved"
        )
        metric_card(
            "Approved",
            str(approved_count),
            "Completed approvals",
        )
    with metric_columns[2]:
        rejected_count = sum(
            1
            for item in reviewed
            if item["review"]["result"] != "approved"
        )
        metric_card(
            "Rejected",
            str(rejected_count),
            "Completed rejections",
        )

    st.write("")
    pending_tab, history_tab = st.tabs(
        ["Pending decisions", "Review history"]
    )

    with pending_tab:
        if not pending_reviews:
            st.success("No payments are awaiting manual approval.")

        for item in pending_reviews:
            decision = item["decision"]
            payment_id = item["payment_id"]

            with st.expander(
                f'{item["invoice_id"]}  ·  '
                f'{item["customer_name"]}  ·  '
                f'{format_currency(item["amount"])}',
                expanded=True,
            ):
                detail_columns = st.columns(2)
                detail_columns[0].markdown(
                    f'**Failure reason**  \n{item["failure_reason"]}'
                )
                detail_columns[1].markdown(
                    f'**Policy decision**  \n{decision["reason"]}'
                )

                with st.form(
                    key=f"manual-review-form-{payment_id}"
                ):
                    reviewer = st.text_input(
                        "Reviewer name",
                        value="StudioPay Reviewer",
                        key=f"reviewer-{payment_id}",
                    )

                    approval_columns = st.columns(2)
                    approve_clicked = approval_columns[0].form_submit_button(
                        "Approve recovery",
                        use_container_width=True,
                        type="primary",
                    )
                    reject_clicked = approval_columns[1].form_submit_button(
                        "Reject recovery",
                        use_container_width=True,
                    )

                if approve_clicked or reject_clicked:
                    if len(reviewer.strip()) < 2:
                        st.error("Enter a valid reviewer name.")
                    else:
                        try:
                            submit_manual_review(
                                payment_id=payment_id,
                                approved=approve_clicked,
                                reviewer=reviewer.strip(),
                            )
                            st.cache_data.clear()
                            st.toast("Review recorded successfully.")
                            st.rerun()
                        except requests.RequestException as error:
                            st.error(
                                "Review failed: "
                                + get_request_error_message(error)
                            )

    with history_tab:
        if not reviewed:
            st.info("No completed manual reviews yet.")

        for item in reviewed:
            review = item["review"]
            result = review["result"]

            with st.expander(
                f'{item["invoice_id"]}  ·  {result.title()}'
            ):
                if result == "approved":
                    st.success("Manual recovery approved.")
                else:
                    st.error("Manual recovery rejected.")

                detail_columns = st.columns(3)
                detail_columns[0].markdown(
                    f'**Customer**  \n{item["customer_name"]}'
                )
                detail_columns[1].markdown(
                    f'**Amount**  \n{format_currency(item["amount"])}'
                )
                detail_columns[2].markdown(
                    f'**Reviewer**  \n{review["reviewer"]}'
                )
                st.caption(
                    "Reviewed "
                    + format_ist_datetime(review.get("reviewed_at"))
                )


def render_audit_trail(audit_events):
    render_hero(
        "Traceable by design",
        "Recovery Audit Trail",
        (
            "Inspect policy decisions, approvals, Razorpay actions and "
            "recovery outcomes in chronological order."
        ),
    )

    audit_dataframe = pd.DataFrame(audit_events)

    if audit_dataframe.empty:
        st.info("No audit events have been recorded.")
        return

    if "created_at" in audit_dataframe.columns:
        audit_dataframe["created_at"] = pd.to_datetime(
            audit_dataframe["created_at"],
            errors="coerce",
            utc=True,
        ).dt.tz_convert("Asia/Kolkata")

    filter_column, search_column = st.columns([1, 2])

    event_options = ["All"]
    if "event_type" in audit_dataframe.columns:
        event_options.extend(
            sorted(
                audit_dataframe["event_type"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )

    with filter_column:
        selected_event = st.selectbox(
            "Event type",
            event_options,
            key="audit-event-filter",
        )

    with search_column:
        audit_search = st.text_input(
            "Search invoice, actor or decision",
            placeholder="Search the audit trail",
            key="audit-search",
        ).strip()

    if selected_event != "All":
        audit_dataframe = audit_dataframe[
            audit_dataframe["event_type"] == selected_event
        ]

    if audit_search:
        search_mask = pd.Series(
            False,
            index=audit_dataframe.index,
        )

        for column in ["invoice_id", "actor", "decision"]:
            if column in audit_dataframe.columns:
                search_mask |= (
                    audit_dataframe[column]
                    .fillna("")
                    .astype(str)
                    .str.contains(
                        audit_search,
                        case=False,
                        regex=False,
                    )
                )

        audit_dataframe = audit_dataframe[search_mask]

    if audit_dataframe.empty:
        st.info("No audit events match the selected filters.")
        return

    audit_display_columns = [
        column
        for column in [
            "created_at",
            "invoice_id",
            "event_type",
            "actor",
            "decision",
        ]
        if column in audit_dataframe.columns
    ]

    st.dataframe(
        audit_dataframe[audit_display_columns],
        use_container_width=True,
        hide_index=True,
        height=min(650, 74 + len(audit_dataframe) * 35),
        column_config={
            "created_at": st.column_config.DatetimeColumn(
                "Time",
                format="DD MMM YYYY, hh:mm:ss a",
            ),
            "invoice_id": "Invoice",
            "event_type": "Event",
            "actor": "Actor",
            "decision": "Decision",
        },
    )


def render_agent():
    render_hero(
        "Grounded in ClickHouse data",
        "StudioPay Recovery Agent",
        (
            "Ask about failed payments, recovery actions, approval needs "
            "and revenue at risk without leaving the operations console."
        ),
    )

    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I can analyze StudioPay payment data and "
                    "explain recommended recovery actions."
                ),
            }
        ]

    toolbar_left, toolbar_right = st.columns([4, 1])
    with toolbar_left:
        st.caption(
            "The assistant can explain data and policies; recovery actions "
            "remain in the Recovery Center."
        )
    with toolbar_right:
        if st.button(
            "Clear conversation",
            use_container_width=True,
        ):
            st.session_state.agent_messages = [
                {
                    "role": "assistant",
                    "content": (
                        "Conversation cleared. What would you like to "
                        "know about payment recovery?"
                    ),
                }
            ]
            st.rerun()

    chat_container = st.container(height=500)

    with chat_container:
        for chat_message in st.session_state.agent_messages:
            with st.chat_message(chat_message["role"]):
                st.markdown(chat_message["content"])

                if chat_message.get("metadata"):
                    st.caption(chat_message["metadata"])

    user_message = st.chat_input(
        "Ask StudioPay about failed payments"
    )

    if not user_message:
        return

    st.session_state.agent_messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    try:
        with st.spinner("Analyzing StudioPay payment data..."):
            agent_response = send_agent_message(user_message)

        assistant_message = agent_response["message"]
        metadata = (
            f'Model: {agent_response["model"]} · '
            f'Data source: {agent_response["data_source"]}'
        )

        st.session_state.agent_messages.append(
            {
                "role": "assistant",
                "content": assistant_message,
                "metadata": metadata,
            }
        )
    except requests.RequestException as error:
        error_message = (
            "The recovery agent is currently unavailable. "
            + get_request_error_message(error)
        )
        st.session_state.agent_messages.append(
            {
                "role": "assistant",
                "content": error_message,
            }
        )

    st.rerun()


# ---------------------------------------------------------
# Sidebar and application shell
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="sp-brand">
            <div class="sp-brand-mark">₹</div>
            <div>
                <div class="sp-brand-title">StudioPay</div>
                <div class="sp-brand-subtitle">Revenue Operations</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_page = st.radio(
        "Workspace",
        options=[
            "Overview",
            "Recovery Center",
            "Manual Reviews",
            "Audit Trail",
            "AI Assistant",
        ],
        captions=[
            "KPIs and payment health",
            "Queue and recovery actions",
            "Human approval workflow",
            "Immutable recovery history",
            "Ask questions about your data",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("SYSTEM STATUS")

    try:
        system_status = fetch_system_status()
        status_row("Backend", system_status["backend"])
        status_row("ClickHouse", system_status["clickhouse"])
        status_row("Razorpay", system_status["razorpay"])
        status_row("AI Agent", system_status["huggingface"])
    except requests.RequestException:
        status_row("Backend", False)
        status_row("ClickHouse", False)
        status_row("Razorpay", False)
        status_row("AI Agent", False)

    st.write("")
    if st.button(
        "↻  Refresh workspace",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Backend: {BACKEND_URL}")


# ---------------------------------------------------------
# Load data and render selected page
# ---------------------------------------------------------

if selected_page == "AI Assistant":
    render_agent()
else:
    try:
        with st.spinner("Loading StudioPay workspace..."):
            summary = fetch_summary()
            payments = fetch_payments()
            recommendations = fetch_recommendations()

            audit_events = []
            if selected_page == "Audit Trail":
                audit_events = fetch_audit_events()

    except requests.RequestException as error:
        st.error(
            "Unable to load dashboard data: "
            + get_request_error_message(error)
        )
        st.stop()

    if selected_page == "Overview":
        render_overview(
            summary,
            payments,
            recommendations,
        )
    elif selected_page == "Recovery Center":
        render_recovery_center(recommendations)
    elif selected_page == "Manual Reviews":
        render_manual_reviews(recommendations)
    elif selected_page == "Audit Trail":
        render_audit_trail(audit_events)


st.caption(
    "StudioPay Admin · Policy-governed revenue recovery · "
    f"Last rendered {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
)
