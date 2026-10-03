#!/usr/bin/env bash
# Move REDDIT_* entries from the project .env into the shared credentials file
# (default: ~/.config/secrets/reddit.env, override with SHARED_ENV_FILE) so other
# projects and tools can use the same Reddit credentials.
#
# Usage: scripts/move-reddit-creds-to-shared.sh [path/to/project/.env]
#
# Safe to re-run. Never prints secret values, only key names.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ENV="${1:-$(cd "${SCRIPT_DIR}/.." && pwd)/.env}"
SHARED_ENV="${SHARED_ENV_FILE:-${XDG_CONFIG_HOME:-$HOME/.config}/secrets/reddit.env}"

if [[ ! -f "$PROJECT_ENV" ]]; then
    echo "Error: project env file not found: $PROJECT_ENV" >&2
    exit 1
fi

umask 077
mkdir -p "$(dirname "$SHARED_ENV")"
chmod 700 "$(dirname "$SHARED_ENV")"
touch "$SHARED_ENV"
chmod 600 "$SHARED_ENV"

python3 - "$PROJECT_ENV" "$SHARED_ENV" <<'PY'
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

project_path = Path(sys.argv[1])
shared_path = Path(sys.argv[2])

# Values are copied verbatim (quotes and escapes included) so the shared file
# means exactly what the project file meant; no re-quoting.
LINE = re.compile(r"^\s*(?:export\s+)?(REDDIT_[A-Za-z0-9_]+)\s*=\s*(.*?)\s*$")


def parse(lines):
    found = {}
    for index, line in enumerate(lines):
        match = LINE.match(line)
        if match:
            found[match.group(1)] = (index, match.group(2))
    return found


project_lines = project_path.read_text(encoding="utf-8").splitlines()
shared_lines = shared_path.read_text(encoding="utf-8").splitlines()
project_entries = parse(project_lines)
shared_entries = parse(shared_lines)

to_append = []
to_comment = []
conflicts = []

for key, (index, value) in project_entries.items():
    if key not in shared_entries:
        to_append.append(f"{key}={value}")
        to_comment.append(index)
        print(f"moved: {key}")
    elif shared_entries[key][1] == value:
        to_comment.append(index)
        print(f"already shared: {key}")
    else:
        conflicts.append(key)
        print(f"kept in project .env (shared file has a different value): {key}")

if to_append:
    with shared_path.open("a", encoding="utf-8") as handle:
        if shared_lines and shared_lines[-1].strip():
            handle.write("\n")
        handle.write("\n".join(to_append) + "\n")

if to_comment:
    backup = project_path.with_name(f"{project_path.name}.bak.{datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(project_path, backup)
    backup.chmod(0o600)
    for index in to_comment:
        project_lines[index] = f"# moved to {shared_path}: {project_lines[index].split('=', 1)[0].strip()}"
    project_path.write_text("\n".join(project_lines) + "\n", encoding="utf-8")
    print(f"backup: {backup}")

if not project_entries:
    print("nothing to move: no active REDDIT_* entries in project .env")

print(f"shared file: {shared_path}")
if conflicts:
    print("resolve conflicts by editing either file, then re-run")
PY
