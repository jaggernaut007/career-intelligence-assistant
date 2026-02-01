#!/bin/bash

# Career Intelligence Assistant - Docker Compose Runner
# Usage: ./run-docker.sh [command]
# Commands: up, down, build, logs, restart, clean

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Load environment variables from backend/.env if it exists
load_env() {
    if [ -f "./backend/.env" ]; then
        print_status "Loading environment variables from backend/.env"
        export $(grep -v '^#' ./backend/.env | xargs)
    else
        print_warning "No .env file found in backend/. Using default values."
    fi
}

# Start services
up() {
    print_status "Starting Career Intelligence Assistant..."
    load_env
    docker compose up -d
    print_status "Services started!"
    echo ""
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    print_status "Run './run-docker.sh logs' to view logs"
}

# Start with build
up_build() {
    print_status "Building and starting Career Intelligence Assistant..."
    load_env
    docker compose up -d --build
    print_status "Services built and started!"
    echo ""
    echo "  Frontend: http://localhost:5173"
    echo "  Backend:  http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
}

# Stop services
down() {
    print_status "Stopping Career Intelligence Assistant..."
    docker compose down
    print_status "Services stopped."
}

# View logs
logs() {
    docker compose logs -f
}

# Restart services
restart() {
    print_status "Restarting Career Intelligence Assistant..."
    docker compose restart
    print_status "Services restarted."
}

# Build images
build() {
    print_status "Building Docker images..."
    docker compose build
    print_status "Build complete."
}

# Clean up everything
clean() {
    print_warning "This will remove all containers, volumes, and images for this project."
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker compose down -v --rmi local
        print_status "Cleanup complete."
    else
        print_status "Cleanup cancelled."
    fi
}

# Show status
status() {
    docker compose ps
}

# Show help
show_help() {
    echo "Career Intelligence Assistant - Docker Runner"
    echo ""
    echo "Usage: ./run-docker.sh [command]"
    echo ""
    echo "Commands:"
    echo "  up        Start all services"
    echo "  up-build  Build and start all services"
    echo "  down      Stop all services"
    echo "  build     Build Docker images"
    echo "  logs      Follow logs from all services"
    echo "  restart   Restart all services"
    echo "  status    Show status of services"
    echo "  clean     Remove containers, volumes, and images"
    echo "  help      Show this help message"
    echo ""
}

# Main
check_docker

case "${1:-up}" in
    up)
        up
        ;;
    up-build)
        up_build
        ;;
    down)
        down
        ;;
    build)
        build
        ;;
    logs)
        logs
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
