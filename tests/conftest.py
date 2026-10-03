import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Point env loading at empty files before any test module imports app.config,
# so a developer's real .env or shared credentials file never leaks into tests.
_EMPTY_ENV_DIR = Path(tempfile.mkdtemp(prefix="community-research-tests-"))
_EMPTY_PROJECT_ENV = _EMPTY_ENV_DIR / "project.env"
_EMPTY_SHARED_ENV = _EMPTY_ENV_DIR / "shared.env"
_EMPTY_PROJECT_ENV.touch()
_EMPTY_SHARED_ENV.touch(mode=0o600)
os.environ["ENV_FILE"] = str(_EMPTY_PROJECT_ENV)
os.environ["SHARED_ENV_FILE"] = str(_EMPTY_SHARED_ENV)


@pytest.fixture(autouse=True)
def isolated_env_files(monkeypatch):
    # load_environment() writes straight into os.environ, so restore it wholesale.
    environ_snapshot = dict(os.environ)
    monkeypatch.setenv("ENV_FILE", str(_EMPTY_PROJECT_ENV))
    monkeypatch.setenv("SHARED_ENV_FILE", str(_EMPTY_SHARED_ENV))

    from app.config import get_runtime_config

    get_runtime_config.cache_clear()
    yield
    get_runtime_config.cache_clear()
    os.environ.clear()
    os.environ.update(environ_snapshot)
