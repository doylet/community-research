import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "move-reddit-creds-to-shared.sh"
SECRET = "s3cr3t-value-123"


@pytest.fixture
def sandbox(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    project_env = tmp_path / "project" / ".env"
    project_env.parent.mkdir()
    project_env.write_text(
        'REDDIT_CLIENT_ID="client-id-abc"\n'
        f'REDDIT_CLIENT_SECRET="{SECRET}"\n'
        "MCP_MAX_COMMENTS=50\n"
    )
    env = {k: v for k, v in os.environ.items() if k not in {"SHARED_ENV_FILE", "XDG_CONFIG_HOME"}}
    env["HOME"] = str(home)
    return home, project_env, env


def run(project_env, env):
    return subprocess.run(
        ["bash", str(SCRIPT), str(project_env)],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_first_run_moves_credentials(sandbox):
    home, project_env, env = sandbox

    result = run(project_env, env)

    shared = home / ".config" / "secrets" / "reddit.env"
    assert mode(shared.parent) == 0o700
    assert mode(shared) == 0o600
    shared_text = shared.read_text()
    assert 'REDDIT_CLIENT_ID="client-id-abc"' in shared_text
    assert f'REDDIT_CLIENT_SECRET="{SECRET}"' in shared_text

    project_text = project_env.read_text()
    assert SECRET not in project_text
    assert "MCP_MAX_COMMENTS=50" in project_text
    assert not any(line.startswith("REDDIT_") for line in project_text.splitlines())

    backups = list(project_env.parent.glob(".env.bak.*"))
    assert len(backups) == 1
    assert mode(backups[0]) == 0o600
    assert SECRET in backups[0].read_text()

    assert SECRET not in result.stdout + result.stderr
    assert "moved: REDDIT_CLIENT_SECRET" in result.stdout


def test_rerun_is_idempotent(sandbox):
    home, project_env, env = sandbox
    run(project_env, env)
    shared = home / ".config" / "secrets" / "reddit.env"
    shared_before = shared.read_text()
    project_before = project_env.read_text()

    result = run(project_env, env)

    assert shared.read_text() == shared_before
    assert project_env.read_text() == project_before
    assert shared_before.count("REDDIT_CLIENT_ID=") == 1
    assert SECRET not in result.stdout + result.stderr


def test_conflicting_shared_value_is_left_alone(sandbox):
    home, project_env, env = sandbox
    shared = home / ".config" / "secrets" / "reddit.env"
    shared.parent.mkdir(parents=True)
    shared.write_text('REDDIT_CLIENT_ID="different-id"\n')

    result = run(project_env, env)

    assert 'REDDIT_CLIENT_ID="different-id"' in shared.read_text()
    assert shared.read_text().count("REDDIT_CLIENT_ID=") == 1
    assert 'REDDIT_CLIENT_ID="client-id-abc"' in project_env.read_text()
    assert "kept in project .env" in result.stdout


def test_honours_shared_env_file(sandbox, tmp_path):
    _, project_env, env = sandbox
    custom = tmp_path / "custom" / "creds.env"
    env["SHARED_ENV_FILE"] = str(custom)

    run(project_env, env)

    assert "REDDIT_CLIENT_SECRET=" in custom.read_text()


def test_shared_file_is_loadable_by_app(sandbox, monkeypatch):
    home, project_env, env = sandbox
    run(project_env, env)

    import app.config as config

    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("SHARED_ENV_FILE", str(home / ".config" / "secrets" / "reddit.env"))
    config.load_environment()

    assert config.get_runtime_config().reddit_client_secret == SECRET


def test_special_characters_survive_round_trip(sandbox):
    from dotenv import dotenv_values

    home, project_env, env = sandbox
    project_env.write_text(
        "REDDIT_PASSWORD=\"a\\\"b'c\\\\d\"\n"
        "export REDDIT_USER_AGENT='literal $HOME agent'\n"
        "REDDIT_CLIENT_ID=plain-value\n"
    )
    expected = dotenv_values(project_env)

    run(project_env, env)

    shared = home / ".config" / "secrets" / "reddit.env"
    assert dotenv_values(shared) == expected


def test_shared_file_can_be_sourced_by_shell(sandbox):
    home, project_env, env = sandbox
    run(project_env, env)
    shared = home / ".config" / "secrets" / "reddit.env"

    sourced = subprocess.run(
        ["bash", "-c", f'set -a; source "{shared}"; printf %s "$REDDIT_CLIENT_SECRET"'],
        capture_output=True, text=True, check=True,
    )
    assert sourced.stdout == SECRET
