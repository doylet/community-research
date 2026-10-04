import re
from pathlib import Path

from app.errors import ErrorCode

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ERRORS = ROOT / "frontend" / "lib" / "api-errors.ts"


def backend_error_codes():
    return {value for name, value in vars(ErrorCode).items() if not name.startswith("_")}


def frontend_error_codes():
    source = FRONTEND_ERRORS.read_text()
    table = re.search(r"const ERROR_CODE_NOTIFICATIONS[^=]*= \{(.*?)\n\}", source, re.DOTALL)
    assert table, "ERROR_CODE_NOTIFICATIONS table not found in api-errors.ts"
    return set(re.findall(r"^  ([A-Z_]+): \{", table.group(1), re.MULTILINE))


def test_frontend_has_notification_for_every_error_code():
    missing = backend_error_codes() - frontend_error_codes()
    assert not missing, f"frontend/lib/api-errors.ts has no notification for: {sorted(missing)}"
