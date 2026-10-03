import logging
import os

import pytest

import app.config as config
from app.config import ConfigurationError, get_runtime_config, load_environment

SECRET = "super-secret-value"


@pytest.fixture
def clean_reddit_env(monkeypatch):
    for key in ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT", "MARKER"):
        monkeypatch.delenv(key, raising=False)


def write_env(path, mode=0o600, **values):
    path.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
    path.chmod(mode)
    return path


def test_default_project_file_is_anchored_to_project_root():
    expected = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    assert str(config.DEFAULT_PROJECT_ENV_FILE) == expected


def test_project_file_resolution_ignores_working_directory(tmp_path, monkeypatch, clean_reddit_env):
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    write_env(cwd / ".env", MARKER="from-cwd")
    root_env = write_env(tmp_path / "root.env", MARKER="from-project-root")

    monkeypatch.chdir(cwd)
    monkeypatch.delenv("ENV_FILE")
    monkeypatch.setattr(config, "DEFAULT_PROJECT_ENV_FILE", root_env)

    load_environment()

    assert os.environ["MARKER"] == "from-project-root"


def test_env_file_override(tmp_path, monkeypatch, clean_reddit_env):
    monkeypatch.setenv("ENV_FILE", str(write_env(tmp_path / "alt.env", REDDIT_USER_AGENT="alt-agent")))

    load_environment()

    assert get_runtime_config().reddit_user_agent == "alt-agent"


@pytest.mark.parametrize("variable", ["ENV_FILE", "SHARED_ENV_FILE"])
def test_explicit_missing_file_raises_naming_path(tmp_path, monkeypatch, variable):
    missing = tmp_path / "does-not-exist.env"
    monkeypatch.setenv(variable, str(missing))

    with pytest.raises(ConfigurationError) as exc_info:
        load_environment()

    assert str(missing) in str(exc_info.value)
    assert variable in str(exc_info.value)


def test_absent_default_files_are_fine(tmp_path, monkeypatch):
    monkeypatch.delenv("ENV_FILE")
    monkeypatch.delenv("SHARED_ENV_FILE")
    monkeypatch.setattr(config, "DEFAULT_PROJECT_ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))

    assert load_environment() == []


def test_shared_default_path_uses_xdg_config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config.default_shared_env_file() == tmp_path / "secrets" / "reddit.env"


def test_credentials_only_in_shared_file(tmp_path, monkeypatch, clean_reddit_env):
    monkeypatch.setenv("SHARED_ENV_FILE", str(write_env(tmp_path / "shared.env", REDDIT_CLIENT_ID="shared-id")))

    load_environment()

    assert get_runtime_config().reddit_client_id == "shared-id"


def test_precedence_process_then_project_then_shared(tmp_path, monkeypatch, clean_reddit_env):
    monkeypatch.setenv("REDDIT_CLIENT_ID", "from-process")
    monkeypatch.setenv(
        "ENV_FILE",
        str(write_env(tmp_path / "project.env", REDDIT_CLIENT_ID="from-project", REDDIT_USER_AGENT="project-agent")),
    )
    monkeypatch.setenv(
        "SHARED_ENV_FILE",
        str(write_env(
            tmp_path / "shared.env",
            REDDIT_CLIENT_ID="from-shared",
            REDDIT_USER_AGENT="shared-agent",
            REDDIT_CLIENT_SECRET="shared-secret",
        )),
    )

    load_environment()
    runtime = get_runtime_config()

    assert runtime.reddit_client_id == "from-process"
    assert runtime.reddit_user_agent == "project-agent"
    assert runtime.reddit_client_secret == "shared-secret"


def test_loose_shared_file_permissions_warn_without_values(tmp_path, monkeypatch, caplog, clean_reddit_env):
    shared = write_env(tmp_path / "shared.env", mode=0o644, REDDIT_CLIENT_SECRET=SECRET)
    monkeypatch.setenv("SHARED_ENV_FILE", str(shared))

    with caplog.at_level(logging.WARNING, logger="app.config"):
        load_environment()

    assert str(shared) in caplog.text
    assert "chmod 600" in caplog.text
    assert SECRET not in caplog.text
    assert os.environ["REDDIT_CLIENT_SECRET"] == SECRET


def test_strict_shared_file_permissions_do_not_warn(tmp_path, monkeypatch, caplog, clean_reddit_env):
    monkeypatch.setenv("SHARED_ENV_FILE", str(write_env(tmp_path / "shared.env", REDDIT_CLIENT_ID="x")))

    with caplog.at_level(logging.WARNING, logger="app.config"):
        load_environment()

    assert caplog.text == ""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(None, 32), ("0", 0), ("10", 10), ("none", None), ("NONE", None)],
)
def test_replace_more_limit_parsing(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv("REDDIT_REPLACE_MORE_LIMIT", raising=False)
    else:
        monkeypatch.setenv("REDDIT_REPLACE_MORE_LIMIT", raw)

    assert get_runtime_config().replace_more_limit == expected


@pytest.mark.parametrize("raw", ["-1", "lots", "1.5"])
def test_invalid_replace_more_limit_names_variable(monkeypatch, raw):
    monkeypatch.setenv("REDDIT_REPLACE_MORE_LIMIT", raw)

    with pytest.raises(ValueError, match="REDDIT_REPLACE_MORE_LIMIT"):
        get_runtime_config()


def test_load_dotenv_only_called_from_config():
    root = config.PROJECT_ROOT
    sources = list((root / "app").glob("*.py")) + [root / "mcp_server.py", root / "main.py"]
    callers = sorted(p.name for p in sources if "load_dotenv(" in p.read_text())
    assert callers == ["config.py"]
