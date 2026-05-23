#!/usr/bin/env bash
# Wires up the pre-commit framework hook into .git/hooks/pre-commit, chaining
# with the existing beads (bd) pre-commit hook if present.
#
# Idempotent: re-running is safe.
#
# Usage: bash scripts/install-git-hooks.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"
SENTINEL="# pre-commit framework chain: 2026-05-23"

if ! command -v pre-commit >/dev/null 2>&1; then
    echo "ERROR: pre-commit not found in PATH." >&2
    echo "Install with: pip install pre-commit  (or use uv/mise/pipx)" >&2
    exit 1
fi

if [ ! -f "$REPO_ROOT/.pre-commit-config.yaml" ]; then
    echo "ERROR: .pre-commit-config.yaml not found at repo root." >&2
    exit 1
fi

# Case 1: no existing hook. Run pre-commit install as-is.
if [ ! -f "$HOOK" ]; then
    echo "No existing pre-commit hook. Running pre-commit install."
    pre-commit install
    exit 0
fi

# Case 2: hook exists and already contains our sentinel. Idempotent skip.
if grep -q "$SENTINEL" "$HOOK"; then
    echo "Hook already chained. No changes."
    exit 0
fi

# Case 3: hook exists but no sentinel. Only modify if it is the known beads hook.
if ! grep -q "bd (beads) pre-commit hook" "$HOOK"; then
    echo "ERROR: Existing pre-commit hook is not the expected beads hook." >&2
    echo "Refusing to modify. Inspect $HOOK manually, then either:" >&2
    echo "  (a) add the framework call yourself, or" >&2
    echo "  (b) remove the hook and re-run this script." >&2
    exit 1
fi

# Backup before modifying.
BACKUP="$HOOK.backup-$(date +%Y%m%d-%H%M%S)"
cp "$HOOK" "$BACKUP"
echo "Backed up existing hook to: $BACKUP"

# Insert the framework call before the final 'exit 0'.
TMP="$(mktemp)"
awk -v sentinel="$SENTINEL" '
/^exit 0$/ && !done {
    print ""
    print sentinel
    print "# Run pre-commit framework hooks (detect-secrets, ruff, mypy, bandit, etc.)."
    print "if command -v pre-commit >/dev/null 2>&1 && [ -f \"$(git rev-parse --show-toplevel)/.pre-commit-config.yaml\" ]; then"
    print "    pre-commit run --hook-stage pre-commit"
    print "    PC_EXIT=$?"
    print "    if [ \"$PC_EXIT\" -ne 0 ]; then"
    print "        exit \"$PC_EXIT\""
    print "    fi"
    print "fi"
    print ""
    done = 1
}
{ print }
' "$HOOK" > "$TMP"

mv "$TMP" "$HOOK"
chmod +x "$HOOK"
echo "Modified $HOOK to chain pre-commit framework after beads."
echo "To verify: run 'bash $HOOK' and check exit 0."
