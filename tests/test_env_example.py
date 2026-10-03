import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / ".env.example"

ENV_NAME = re.compile(r'(?:os\.getenv|_env_[a-z_]+|_resolve_env_file)\(\s*"([A-Z][A-Z0-9_]*)"')
CREDENTIAL_KEYS = {"REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"}
PLACEHOLDER = re.compile(r'^"?(your_[a-z_]+|)"?$')


def env_names_read_by_code():
    sources = list((ROOT / "app").glob("*.py")) + [ROOT / "mcp_server.py"]
    return {name for path in sources for name in ENV_NAME.findall(path.read_text())}


def test_env_example_documents_every_variable():
    example = EXAMPLE.read_text()
    names = env_names_read_by_code()

    assert "REDDIT_CLIENT_ID" in names  # sanity check the scanner
    missing = sorted(name for name in names if not re.search(rf"\b{name}\b", example))
    assert missing == []


def test_env_example_credentials_are_placeholders():
    for line in EXAMPLE.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key in CREDENTIAL_KEYS:
            assert PLACEHOLDER.match(value), f"{key} in .env.example must be a placeholder"
