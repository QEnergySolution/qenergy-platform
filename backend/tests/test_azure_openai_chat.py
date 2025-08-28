import os
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv


def test_send_simple_chat_request_to_azure_openai():
    env_path = Path("/Users/yuxin.xue/Projects/qenergy-platform/backend/.env")
    assert env_path.exists(), f".env not found at {env_path}"
    load_dotenv(env_path)

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    if not (api_key and endpoint and deployment):
        pytest.skip("AZURE_OPENAI_* environment not fully configured")

    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Give me a two-line haiku about wind farms."},
        ],
        "temperature": 0.5,
        "max_tokens": 64,
    }

    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert "choices" in data and data["choices"], f"Unexpected response: {data}"
        content = data["choices"][0]["message"]["content"].strip()
        assert content, "Empty content from model"
        # Print the model output for easy inspection
        print("\nAzure OpenAI response:\n" + content + "\n")


