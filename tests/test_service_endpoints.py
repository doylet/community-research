import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SERVICES_TABLE = ROOT / "deploy" / "services.yaml"
BLUEPRINT = ROOT / "render.yaml"
ONRENDER_HOST = re.compile(r"\b([a-z0-9][a-z0-9-]*\.onrender\.com)\b")
SCANNED_PATHS = [
    "app",
    "mcp_server.py",
    "frontend/app",
    "frontend/components",
    "frontend/lib",
    "install-claude-fetch-reddit.sh",
    "README.md",
    "render.yaml",
]


def services_table():
    return yaml.safe_load(SERVICES_TABLE.read_text())


def blueprint_services():
    return {service["name"]: service for service in yaml.safe_load(BLUEPRINT.read_text())["services"]}


def env_vars(service):
    return {item["key"]: item.get("value") for item in service.get("envVars", [])}


def tracked_files():
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "--", *SCANNED_PATHS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [ROOT / line for line in output.splitlines() if (ROOT / line).is_file()]


def test_services_table_matches_production():
    assert services_table() == {
        "community-research-api": "community-research.onrender.com",
        "community-research": "community-research-frontend.onrender.com",
        "community-research-mcp": "community-research-mcp.onrender.com",
    }


def test_blueprint_names_match_dashboard_names():
    assert set(blueprint_services()) == set(services_table())


def test_blueprint_roles_use_expected_names():
    services = blueprint_services()
    assert services["community-research-api"]["startCommand"].startswith("gunicorn main:app")
    assert services["community-research"]["rootDir"] == "frontend"
    assert services["community-research-mcp"]["startCommand"] == "python mcp_server.py"


def test_every_onrender_host_is_a_known_service():
    known_hosts = set(services_table().values())
    unknown = []
    for path in tracked_files():
        for host in ONRENDER_HOST.findall(path.read_text(errors="ignore")):
            if host not in known_hosts:
                unknown.append(f"{path.relative_to(ROOT)}: {host}")
    assert unknown == []


def test_api_url_consumers_point_at_api_host():
    api_url = f"https://{services_table()['community-research-api']}"
    services = blueprint_services()

    assert env_vars(services["community-research-mcp"])["COMMUNITY_RESEARCH_API_URL"] == api_url
    frontend_env = env_vars(services["community-research"])
    assert frontend_env["COMMUNITY_RESEARCH_API_URL"] == api_url
    assert "NEXT_PUBLIC_API_URL" not in frontend_env


def test_url_env_vars_use_known_hosts():
    known_hosts = set(services_table().values())
    for name, service in blueprint_services().items():
        for key, value in env_vars(service).items():
            if isinstance(value, str) and value.startswith("http"):
                host = re.sub(r"^https?://", "", value).split("/")[0]
                assert host in known_hosts, f"{name}.{key} uses unknown host {host}"


def test_stale_blueprint_removed():
    assert not (ROOT / ".render.yaml").exists()


def test_blueprint_retry_attempts_match_code_default():
    value = env_vars(blueprint_services()["community-research-mcp"]).get("MCP_API_RETRY_ATTEMPTS")
    assert value in (None, 1, "1")
