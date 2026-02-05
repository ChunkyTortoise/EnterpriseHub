#!/usr/bin/env bash
set -euo pipefail

curl -fsS "http://localhost:8000/health" >/dev/null 2>&1 || exit 1
echo "healthy"
