#!/usr/bin/env bash
set -e

# Career Intelligence Assistant — Session Initialisation Script
# Run at the start of every session to verify the app is in a working state.

PASS="✅"
FAIL="❌"
WARN="⚠️"
RESULTS=()

check() {
    local label="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "$PASS $label"
        RESULTS+=("PASS")
    else
        echo "$FAIL $label"
        RESULTS+=("FAIL")
        return 1
    fi
}

warn_check() {
    local label="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "$PASS $label"
        RESULTS+=("PASS")
    else
        echo "$WARN $label (optional — continuing)"
        RESULTS+=("WARN")
    fi
}

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================"
echo "  Career Intelligence Assistant — Init Check"
echo "============================================"
echo ""

# 1. Environment check
echo "--- Environment ---"
warn_check ".env file exists" test -f .env
warn_check ".env.example exists" test -f .env.example

# 2. Backend dependency check
echo ""
echo "--- Backend Dependencies ---"
if command -v python3 &> /dev/null; then
    echo "$PASS Python3 found: $(python3 --version 2>&1)"
    RESULTS+=("PASS")
else
    echo "$FAIL Python3 not found"
    RESULTS+=("FAIL")
fi

if [ -d "venv" ] || [ -d "backend/.venv" ]; then
    echo "$PASS Virtual environment exists"
    RESULTS+=("PASS")
else
    echo "$WARN No virtual environment found"
    RESULTS+=("WARN")
fi

# 3. Frontend dependency check
echo ""
echo "--- Frontend Dependencies ---"
warn_check "Node.js installed" command -v node
if [ -d "frontend/node_modules" ]; then
    echo "$PASS frontend/node_modules exists"
    RESULTS+=("PASS")
else
    echo "$WARN frontend/node_modules missing — run: cd frontend && npm install"
    RESULTS+=("WARN")
fi

# 4. Backend lint check
echo ""
echo "--- Backend Lint ---"
if command -v ruff &> /dev/null; then
    check "ruff check backend/" ruff check backend/ --quiet
elif [ -f "venv/bin/ruff" ]; then
    check "ruff check backend/" ./venv/bin/ruff check backend/ --quiet
else
    echo "$WARN ruff not found — install with: pip install ruff"
    RESULTS+=("WARN")
fi

# 5. Backend tests
echo ""
echo "--- Backend Tests ---"
if command -v pytest &> /dev/null; then
    check "pytest tests/unit/" pytest backend/tests/unit/ -v --tb=short -q 2>&1
elif [ -f "venv/bin/pytest" ]; then
    check "pytest tests/unit/" ./venv/bin/pytest backend/tests/unit/ -v --tb=short -q 2>&1
else
    echo "$WARN pytest not found — install with: pip install pytest"
    RESULTS+=("WARN")
fi

# 6. Frontend lint check
echo ""
echo "--- Frontend Lint ---"
if [ -d "frontend/node_modules" ]; then
    (cd frontend && warn_check "ESLint" npx eslint . --ext ts,tsx --max-warnings 0)
else
    echo "$WARN Skipping frontend lint (node_modules missing)"
    RESULTS+=("WARN")
fi

# 7. Frontend tests
echo ""
echo "--- Frontend Tests ---"
if [ -d "frontend/node_modules" ]; then
    (cd frontend && warn_check "Vitest" npx vitest run --reporter=verbose 2>&1)
else
    echo "$WARN Skipping frontend tests (node_modules missing)"
    RESULTS+=("WARN")
fi

# 8. Docker check
echo ""
echo "--- Docker ---"
warn_check "Docker installed" command -v docker
warn_check "docker-compose.yml exists" test -f docker-compose.yml

# Summary
echo ""
echo "============================================"
echo "  Summary"
echo "============================================"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
for r in "${RESULTS[@]}"; do
    case "$r" in
        PASS) ((PASS_COUNT++)) ;;
        FAIL) ((FAIL_COUNT++)) ;;
        WARN) ((WARN_COUNT++)) ;;
    esac
done

echo "$PASS Passed: $PASS_COUNT"
echo "$FAIL Failed: $FAIL_COUNT"
echo "$WARN Warnings: $WARN_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "Fix failures before starting new work."
    exit 1
fi

echo ""
echo "System ready. Proceed with development."
exit 0
