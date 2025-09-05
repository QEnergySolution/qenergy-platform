from pathlib import Path

try:
    from dotenv import load_dotenv
    # Load backend/.env at import time (idempotent). This ensures local runs always pick up env vars.
    _env_path = Path(__file__).resolve().parents[1] / ".env"
    if _env_path.exists():
        # Ensure backend/.env takes precedence over any pre-set shell envs for local runs
        load_dotenv(_env_path, override=True)
except ImportError:
    # python-dotenv not available, skip loading .env file
    pass

__all__ = []


