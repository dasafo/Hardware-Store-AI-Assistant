#!/bin/bash

# 🏪 Hardware Store AI Assistant - Quick Start Script
# This script automates the initial setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${PURPLE}============================================${NC}"
    echo -e "${PURPLE}🏪 $1${NC}"
    echo -e "${PURPLE}============================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the root directory of the Hardware Store AI Assistant project"
    exit 1
fi

print_header "HARDWARE STORE AI ASSISTANT - QUICK START"

print_info "This script will help you set up the Hardware Store AI Assistant quickly"
print_info "Make sure you have Docker and Docker Compose installed"

# Check for Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    print_info "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    print_info "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Docker and Docker Compose are available"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        print_success "Created backend/.env from template"
        print_warning "Please edit backend/.env and add your OpenAI API key"
        print_info "You can get an API key from: https://platform.openai.com/api-keys"
        
        # Ask user if they want to continue without API key
        echo -e "\n${CYAN}Do you want to continue without setting up the OpenAI API key? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Please edit backend/.env with your OpenAI API key and run this script again"
            exit 0
        fi
    else
        print_error "backend/.env.example not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" backend/.env 2>/dev/null; then
    print_warning "OpenAI API key not configured (still using placeholder)"
    print_info "Some AI features may not work without a valid API key"
fi

print_header "STARTING SERVICES"

print_info "Starting all Docker services..."
if make up; then
    print_success "All services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

print_info "Waiting for services to be ready..."
sleep 10

print_header "CHECKING SERVICE HEALTH"

# Check if services are running
print_info "Checking backend health..."
if curl -s http://localhost:8000/health > /dev/null; then
    print_success "Backend is healthy"
else
    print_warning "Backend might still be starting up"
fi

print_info "Checking database connection..."
if curl -s http://localhost:8000/health/postgres > /dev/null; then
    print_success "Database is connected"
else
    print_warning "Database might still be initializing"
fi

print_info "Checking Redis cache..."
if curl -s http://localhost:8000/health/redis > /dev/null; then
    print_success "Redis cache is connected"
else
    print_warning "Redis might still be starting up"
fi

print_info "Checking Qdrant vector database..."
if curl -s http://localhost:8000/health/qdrant > /dev/null; then
    print_success "Qdrant vector database is connected"
else
    print_warning "Qdrant might still be starting up"
fi

print_header "INITIALIZING VECTOR DATABASE"

print_info "Indexing product embeddings into Qdrant..."
if make index-qdrant; then
    print_success "Vector database initialized successfully"
else
    print_warning "Vector database initialization failed or skipped"
    print_info "You can run 'make index-qdrant' later to initialize it"
fi

print_header "RUNNING DEMO"

print_info "Running the interactive demo to test all features..."
if python3 scripts/demo.py; then
    print_success "Demo completed successfully"
else
    print_warning "Demo completed with some issues"
fi

print_header "SETUP COMPLETE! 🎉"

print_success "Hardware Store AI Assistant is now running!"
print_info ""
print_info "🌐 Access Points:"
print_info "   • API Documentation: http://localhost:8000/docs"
print_info "   • n8n Workflows: http://localhost:5678"
print_info "   • Database Admin: http://localhost:5050"
print_info "   • Qdrant Dashboard: http://localhost:6333/dashboard"
print_info ""
print_info "🚀 Quick Test Commands:"
print_info "   • Health Check: curl http://localhost:8000/health"
print_info "   • Search Test: curl -X POST http://localhost:8000/search -H 'Content-Type: application/json' -d '{\"query\":\"hammer\"}'"
print_info "   • Run Demo: python scripts/demo.py"
print_info ""
print_info "📚 Documentation:"
print_info "   • README: View the README.md file"
print_info "   • Roadmap: View docs/ROADMAP.md"
print_info "   • API Docs: http://localhost:8000/docs"
print_info ""
print_info "🛠️  Management Commands:"
print_info "   • View Logs: make logs"
print_info "   • Stop Services: make down"
print_info "   • Restart Services: make restart"
print_info ""

if grep -q "your_openai_api_key_here" backend/.env 2>/dev/null; then
    print_warning "Remember to set your OpenAI API key in backend/.env for full AI functionality"
fi

print_success "Happy building! 🏪🤖" 