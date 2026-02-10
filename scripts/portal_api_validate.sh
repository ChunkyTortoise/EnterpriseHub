#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

run_step() {
  local label="$1"
  shift
  echo "[STEP] $label"
  if "$@"; then
    echo "[PASS] $label"
  else
    echo "[FAIL] $label"
    exit 1
  fi
}

run_step "Lint portal api surface" \
  ruff check \
    main.py \
    portal_api \
    modules \
    scripts/portal_api_client_example.py \
    scripts/portal_api_latency_sanity.py

run_step "Compile portal api bundle" \
  python3 -m py_compile \
    main.py \
    portal_api/app.py \
    portal_api/dependencies.py \
    portal_api/models.py \
    portal_api/routers/root.py \
    portal_api/routers/vapi.py \
    portal_api/routers/portal.py \
    portal_api/routers/ghl.py \
    portal_api/routers/admin.py \
    portal_api/routers/language.py \
    modules/inventory_manager.py \
    modules/ghl_sync.py \
    modules/appointment_manager.py \
    modules/voice_trigger.py \
    scripts/refresh_portal_openapi_snapshot.py \
    scripts/portal_api_client_example.py \
    scripts/portal_api_latency_sanity.py

run_step "Run portal api tests (isolated from root conftest)" \
  pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests
