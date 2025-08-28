import os
from pathlib import Path

from dotenv import load_dotenv


def test_azure_openai_env_vars_present_and_valid():
    env_path = Path("./backend/.env")
    assert env_path.exists(), f".env not found at {env_path}"

    # Explicitly load the backend .env
    load_dotenv(env_path)

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

    assert api_key is not None and len(api_key.strip()) > 0, "AZURE_OPENAI_API_KEY is missing/empty"
    assert endpoint is not None and len(endpoint.strip()) > 0, "AZURE_OPENAI_ENDPOINT is missing/empty"

    # Basic sanity checks for endpoint format (typical: https://<resource>.openai.azure.com)
    assert endpoint.startswith("https://"), "AZURE_OPENAI_ENDPOINT must start with https://"
    assert ("openai.azure.com" in endpoint or endpoint.endswith(".azure.com")), "AZURE_OPENAI_ENDPOINT does not look like an Azure OpenAI endpoint"


