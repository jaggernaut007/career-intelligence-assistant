#!/bin/bash

# Career Intelligence Assistant - Test Runner Script
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VERBOSE=""
COVERAGE=""
SELECTED_TESTS=()

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Career Intelligence Assistant Tests${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_usage() {
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all          Run all tests (unit, integration, contract)"
    echo "  -u, --unit         Run unit tests"
    echo "  -i, --integration  Run integration tests"
    echo "  -c, --contract     Run contract tests"
    echo "  -e, --e2e          Run E2E tests (requires server running)"
    echo "  -E, --evaluation   Run evaluation tests (requires OpenAI API)"
    echo "  -v, --verbose      Verbose output"
    echo "  --coverage         Generate coverage report"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh -a              # Run all standard tests"
    echo "  ./run_tests.sh -u -i           # Run unit and integration tests"
    echo "  ./run_tests.sh -a --coverage   # Run all tests with coverage"
    echo "  ./run_tests.sh -e              # Run E2E tests"
    echo ""
    echo "Test Categories:"
    echo "  unit        - Fast tests with mocked dependencies"
    echo "  integration - Tests with mocked external services"
    echo "  contract    - API schema validation tests"
    echo "  e2e         - End-to-end tests (requires: server, Neo4j, OpenAI)"
    echo "  evaluation  - LLM-as-Judge tests (requires: OpenAI API)"
}

check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: 'uv' is not installed. Please install it first.${NC}"
        echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Check if we're in the backend directory
    if [ ! -f "pyproject.toml" ]; then
        echo -e "${RED}Error: Must run from the backend directory.${NC}"
        exit 1
    fi

    echo -e "${GREEN}Prerequisites OK${NC}"
    echo ""
}

check_env_vars() {
    local test_type=$1
    local missing_vars=()

    case $test_type in
        "e2e")
            [ -z "$NEO4J_URI" ] && missing_vars+=("NEO4J_URI")
            [ -z "$NEO4J_USERNAME" ] && missing_vars+=("NEO4J_USERNAME")
            [ -z "$NEO4J_PASSWORD" ] && missing_vars+=("NEO4J_PASSWORD")
            [ -z "$OPENAI_API_KEY" ] && missing_vars+=("OPENAI_API_KEY")
            [ -z "$HF_TOKEN" ] && missing_vars+=("HF_TOKEN")
            ;;
        "evaluation")
            [ -z "$OPENAI_API_KEY" ] && missing_vars+=("OPENAI_API_KEY")
            ;;
    esac

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${YELLOW}Warning: Missing environment variables for $test_type tests:${NC}"
        for var in "${missing_vars[@]}"; do
            echo -e "  - $var"
        done
        echo ""
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

run_tests() {
    local test_path=$1
    local test_name=$2

    echo -e "${BLUE}Running $test_name...${NC}"
    echo "----------------------------------------"

    local cmd="uv run pytest $test_path"
    [ -n "$VERBOSE" ] && cmd="$cmd -v"
    [ -n "$COVERAGE" ] && cmd="$cmd --cov=app --cov-report=term-missing"

    if eval $cmd; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            SELECTED_TESTS+=("unit" "integration" "contract")
            shift
            ;;
        -u|--unit)
            SELECTED_TESTS+=("unit")
            shift
            ;;
        -i|--integration)
            SELECTED_TESTS+=("integration")
            shift
            ;;
        -c|--contract)
            SELECTED_TESTS+=("contract")
            shift
            ;;
        -e|--e2e)
            SELECTED_TESTS+=("e2e")
            shift
            ;;
        -E|--evaluation)
            SELECTED_TESTS+=("evaluation")
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        --coverage)
            COVERAGE="1"
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# If no tests selected, show interactive menu
if [ ${#SELECTED_TESTS[@]} -eq 0 ]; then
    print_header
    echo "Select tests to run:"
    echo ""
    echo "  1) All standard tests (unit, integration, contract)"
    echo "  2) Unit tests only"
    echo "  3) Integration tests only"
    echo "  4) Contract tests only"
    echo "  5) E2E tests (requires server running)"
    echo "  6) Evaluation tests (requires OpenAI API)"
    echo "  7) All tests including E2E and Evaluation"
    echo "  q) Quit"
    echo ""
    read -p "Enter choice [1-7, q]: " choice

    case $choice in
        1) SELECTED_TESTS=("unit" "integration" "contract") ;;
        2) SELECTED_TESTS=("unit") ;;
        3) SELECTED_TESTS=("integration") ;;
        4) SELECTED_TESTS=("contract") ;;
        5) SELECTED_TESTS=("e2e") ;;
        6) SELECTED_TESTS=("evaluation") ;;
        7) SELECTED_TESTS=("unit" "integration" "contract" "e2e" "evaluation") ;;
        q|Q) echo "Exiting."; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}"; exit 1 ;;
    esac
    echo ""
fi

# Load .env file if it exists
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
elif [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

print_header
check_prerequisites

# Track results
PASSED=0
FAILED=0
FAILED_TESTS=()

# Run selected tests
for test in "${SELECTED_TESTS[@]}"; do
    case $test in
        "unit")
            check_env_vars "unit"
            if run_tests "tests/unit" "Unit Tests"; then
                ((PASSED++))
            else
                ((FAILED++))
                FAILED_TESTS+=("unit")
            fi
            ;;
        "integration")
            if run_tests "tests/integration" "Integration Tests"; then
                ((PASSED++))
            else
                ((FAILED++))
                FAILED_TESTS+=("integration")
            fi
            ;;
        "contract")
            if run_tests "tests/contract" "Contract Tests"; then
                ((PASSED++))
            else
                ((FAILED++))
                FAILED_TESTS+=("contract")
            fi
            ;;
        "e2e")
            check_env_vars "e2e"
            echo -e "${YELLOW}Note: E2E tests require the backend server to be running.${NC}"
            echo -e "${YELLOW}Start it with: uv run uvicorn app.main:app --port 8000${NC}"
            echo ""
            if run_tests "tests/e2e" "E2E Tests"; then
                ((PASSED++))
            else
                ((FAILED++))
                FAILED_TESTS+=("e2e")
            fi
            ;;
        "evaluation")
            check_env_vars "evaluation"
            if run_tests "tests/evaluation" "Evaluation Tests (LLM-as-Judge)"; then
                ((PASSED++))
            else
                ((FAILED++))
                FAILED_TESTS+=("evaluation")
            fi
            ;;
    esac
done

# Generate coverage report if requested
if [ -n "$COVERAGE" ]; then
    echo -e "${BLUE}Generating HTML coverage report...${NC}"
    uv run pytest --cov=app --cov-report=html tests/unit tests/integration tests/contract 2>/dev/null || true
    echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
    echo ""
fi

# Summary
echo "========================================"
echo -e "${BLUE}Test Summary${NC}"
echo "========================================"
echo -e "  Passed: ${GREEN}$PASSED${NC}"
echo -e "  Failed: ${RED}$FAILED${NC}"

if [ $FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed test suites:${NC}"
    for t in "${FAILED_TESTS[@]}"; do
        echo -e "  - $t"
    done
    exit 1
else
    echo ""
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
