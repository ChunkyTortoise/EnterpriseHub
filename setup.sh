#!/usr/bin/env bash
# EnterpriseHub — Deploy in 5 Minutes
# Usage: ./setup.sh
# Requirements: Docker + Docker Compose
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

info()  { printf "${CYAN}[INFO]${NC}  %s\n" "$*"; }
ok()    { printf "${GREEN}[OK]${NC}    %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
fail()  { printf "${RED}[FAIL]${NC}  %s\n" "$*"; exit 1; }

# ── Pre-flight checks ───────────────────────────────────────────────
info "Checking prerequisites..."

command -v docker >/dev/null 2>&1 || fail "Docker is not installed. Install from https://docs.docker.com/get-docker/"

# Accept both "docker compose" (v2 plugin) and "docker-compose" (standalone)
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    fail "Docker Compose is not installed. Install from https://docs.docker.com/compose/install/"
fi

ok "Docker and Compose detected ($COMPOSE)"

# ── Create .env if missing ───────────────────────────────────────────
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        warn "Created .env from .env.example — review and update secrets before production use."
    else
        info "No .env file found. Creating minimal defaults..."
        cat > .env <<'ENVEOF'
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:password@localhost:5432/enterprise_hub
REDIS_URL=redis://localhost:6379
POSTGRES_PASSWORD=password
TEST_MODE=false
ENVEOF
        warn "Created .env with development defaults."
    fi
fi

# ── Step 1: Start containers ────────────────────────────────────────
info "Starting Docker containers..."
$COMPOSE up -d postgres redis
ok "Containers starting."

# ── Step 2: Wait for Postgres health check ──────────────────────────
info "Waiting for PostgreSQL to become healthy..."
RETRIES=30
DELAY=2
for i in $(seq 1 $RETRIES); do
    if docker exec ghl_postgres pg_isready -U postgres -q 2>/dev/null; then
        ok "PostgreSQL is ready (attempt $i/$RETRIES)."
        break
    fi
    if [ "$i" -eq "$RETRIES" ]; then
        fail "PostgreSQL did not become ready after $((RETRIES * DELAY))s. Check 'docker logs ghl_postgres'."
    fi
    sleep $DELAY
done

# ── Step 3: Run Alembic migrations ──────────────────────────────────
info "Running database migrations..."
if [ -f alembic.ini ]; then
    # Prefer running inside the app container if it is up, otherwise locally.
    if docker exec ghl_real_estate_ai alembic --version >/dev/null 2>&1; then
        docker exec ghl_real_estate_ai alembic upgrade head
    elif command -v alembic >/dev/null 2>&1; then
        alembic upgrade head
    else
        warn "Alembic not available locally or in container. Skipping migrations."
        warn "Run 'pip install alembic && alembic upgrade head' manually."
    fi
    ok "Migrations complete."
else
    warn "alembic.ini not found — skipping migrations."
fi

# ── Step 4: Seed demo data ──────────────────────────────────────────
info "Seeding demo data..."
SEED_SCRIPT="scripts/seed_demo_environment.py"
if [ -f "$SEED_SCRIPT" ]; then
    if docker exec ghl_real_estate_ai python "$SEED_SCRIPT" 2>/dev/null; then
        ok "Demo data seeded (via container)."
    elif command -v python3 >/dev/null 2>&1; then
        python3 "$SEED_SCRIPT" || warn "Seed script exited with non-zero status — demo data may be partial."
        ok "Demo data seeded (locally)."
    else
        warn "Python not available. Run 'python3 $SEED_SCRIPT' manually."
    fi
else
    warn "Seed script ($SEED_SCRIPT) not found — skipping."
fi

# ── Step 5: Bring up remaining services ─────────────────────────────
info "Starting application containers..."
$COMPOSE up -d
ok "All containers started."

# ── Done ─────────────────────────────────────────────────────────────
printf "\n"
printf "${GREEN}============================================${NC}\n"
printf "${GREEN}  EnterpriseHub is running!${NC}\n"
printf "${GREEN}============================================${NC}\n"
printf "\n"
printf "  Streamlit BI Dashboard : ${CYAN}http://localhost:8501${NC}\n"
printf "  FastAPI Backend        : ${CYAN}http://localhost:8000${NC}  (if --profile api)\n"
printf "  PostgreSQL             : ${CYAN}localhost:5432${NC}\n"
printf "  Redis                  : ${CYAN}localhost:6379${NC}\n"
printf "\n"
printf "  Stop:    ${YELLOW}$COMPOSE down${NC}\n"
printf "  Logs:    ${YELLOW}$COMPOSE logs -f${NC}\n"
printf "  Tests:   ${YELLOW}pytest --tb=short${NC}\n"
printf "\n"
