import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from app.agent.tools.clickhouse_mcp_tool import (
    get_agent_payment_context,
)
from app.services.policy_service import (
    get_recovery_recommendations,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env", override=True)


SYSTEM_PROMPT = """
You are StudioPay, an AI revenue-recovery assistant.

You receive:
1. Live payment information retrieved through ClickHouse MCP.
2. Recovery recommendations produced by a deterministic policy engine.

Rules:
- Base answers only on the supplied StudioPay data.
- Never invent payment records, amounts, customers or actions.
- Policy decisions are authoritative and cannot be overridden.
- Never claim that an action was executed unless execution is confirmed.
- Clearly mention when manual approval is required.
- Use invoice IDs instead of long payment UUIDs when possible.
- When listing payments, use one concise bullet per payment.
- Include every matching payment before adding explanations.
- Keep the complete response below 250 words.
- Use Indian rupee formatting where appropriate.
"""


def is_huggingface_configured() -> bool:
    return bool(os.getenv("HF_TOKEN"))


async def generate_agent_response(
    user_message: str,
) -> dict[str, str]:
    token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "Qwen/Qwen3-8B")
    provider = os.getenv("HF_PROVIDER", "auto")

    if not token:
        raise RuntimeError("HF_TOKEN is not configured")

    # Live analytics retrieved through official mcp-clickhouse.
    payment_context = await get_agent_payment_context()

    # Decisions remain deterministic and are not created by the LLM.
    recommendations = await asyncio.to_thread(
        get_recovery_recommendations
    )

    studio_context = {
        "clickhouse_mcp_data": payment_context,
        "policy_recommendations": recommendations,
    }

    client = InferenceClient(
        provider=provider,
        api_key=token,
    )

    completion = await asyncio.to_thread(
        client.chat.completions.create,
        model=model,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "/no_think\n\n"
                    "StudioPay context:\n"
                    f"{json.dumps(studio_context, default=str)}"
                    "\n\nUser question:\n"
                    f"{user_message}"
                ),
            },
        ],
        max_tokens=500,
        temperature=0.1,
    )

    content = completion.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Hugging Face returned an empty response"
        )

    return {
        "message": content.strip(),
        "model": model,
        "provider": "huggingface",
        "data_source": "clickhouse-mcp",
    }