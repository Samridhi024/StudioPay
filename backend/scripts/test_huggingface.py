import os
from pathlib import Path
from xml.parsers.expat import model

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def test_huggingface():
    token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "Qwen/Qwen3-8B")
    provider = os.getenv("HF_PROVIDER", "auto")

    if not token:
        raise RuntimeError("HF_TOKEN is missing from the .env file")

    client = InferenceClient(
        provider=provider,
        api_key=token,
    )

    # completion = client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": (
    #                 "You are StudioPay, an AI assistant for "
    #                 "payment recovery operations."
    #             ),
    #         },
    #         {
    #             "role": "user",
    #             "content": "Confirm that the AI connection is working.",
    #         },
    #     ],
    #     max_tokens=60,
    #     temperature=0.1,
    # )

    # response = completion.choices[0].message.content

    # print("Hugging Face connection successful")
    # print(f"Model: {model}")
    # print(f"Response: {response}")
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are StudioPay, an AI assistant for "
                    "payment recovery operations. Give concise answers."
                ),
            },
            {
                "role": "user",
                "content": (
                    "/no_think\n"
                    "Reply exactly: StudioPay AI connection is working."
                ),
            },
        ],
        max_tokens=256,
        temperature=0.1,
    )

    message = completion.choices[0].message
    response = message.content

    if not response:
        print("Full API response:")
        print(completion)
        raise RuntimeError("The model returned no text response")

    print("Hugging Face connection successful")
    print(f"Model: {model}")
    print(f"Response: {response}")


if __name__ == "__main__":
    test_huggingface()