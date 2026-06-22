#!/bin/bash

# ============================================
# DOOMLESS — Groq API Integration Script
# ============================================

# Configuration
GROQ_API_KEY="${GROQ_API_KEY:-YOUR_GROQ_API_KEY}"
BACKEND_URL="http://localhost:8080"
DATA_DIR="./data"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  📊 DOOMLESS — Groq API Integration${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

setup_groq() {
    print_header
    print_info "Setting up Groq API integration..."
    echo ""
    echo "To set up Groq API, you need:"
    echo "  1. A Groq API key from https://console.groq.com"
    echo "  2. Your API key will be stored in .env file"
    echo ""
    
    if [ -f ".env" ]; then
        source .env
        print_info "Found .env file"
    fi
    
    read -p "Enter your Groq API Key: " input_api_key
    
    cat > .env << ENVEOF
# Groq API Configuration
GROQ_API_KEY="${input_api_key:-$GROQ_API_KEY}"
BACKEND_URL="http://localhost:8080"
DATA_DIR="./data"
ENVEOF
    
    mkdir -p "$DATA_DIR"
    
    print_success "Configuration saved to .env"
    print_info "Data will be stored in: $DATA_DIR"
}

export_to_json() {
    print_header
    print_info "Exporting activity history to JSON..."
    
    if [ -f ".env" ]; then
        source .env
    fi
    
    mkdir -p "$DATA_DIR"
    
    print_info "Fetching data from backend..."
    response=$(curl -s "${BACKEND_URL}/history?user_id=1" 2>/dev/null)
    
    if [ -z "$response" ]; then
        print_error "Failed to fetch data from backend"
        echo "Make sure your backend server is running on ${BACKEND_URL}"
        return 1
    fi
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    filename="${DATA_DIR}/export_${timestamp}.json"
    echo "$response" | jq '.' 2>/dev/null > "$filename" || echo "$response" > "$filename"
    
    print_success "Data exported to: $filename"
    
    count=$(cat "$filename" | jq '.history | length' 2>/dev/null || echo "?")
    print_info "Total activities: $count"
}

test_groq_connection() {
    print_header
    print_info "Testing Groq API connection..."
    
    if [ -f ".env" ]; then
        source .env
    fi
    
    if [ "$GROQ_API_KEY" = "YOUR_GROQ_API_KEY" ]; then
        print_error "Groq API key not configured"
        echo "Run: ./sheets.sh setup"
        return 1
    fi
    
    print_info "Testing Groq API with models endpoint..."
    
    response=$(curl -s -X GET "https://api.groq.com/openai/v1/models" \
        -H "Authorization: Bearer $GROQ_API_KEY" \
        -H "Content-Type: application/json" 2>/dev/null)
    
    if echo "$response" | grep -q "object"; then
        print_success "✅ Groq API connection successful!"
        
        echo ""
        print_info "Available Groq models:"
        echo "$response" | jq -r '.data[].id' 2>/dev/null | head -5 || echo "  • llama-3.3-70b-versatile"
        echo "  • llama-3.1-8b-instant"
        echo "  • mixtral-8x7b-32768"
    else
        print_error "❌ Groq API connection failed"
        echo "Please check your API key"
        echo "Get one at: https://console.groq.com"
    fi
}

show_config() {
    print_header
    print_info "Current Configuration"
    echo ""
    
    if [ -f ".env" ]; then
        source .env
        echo "  GROQ_API_KEY: ${GROQ_API_KEY:0:8}... (hidden)"
        echo "  BACKEND_URL: ${BACKEND_URL:-Not set}"
        echo "  DATA_DIR: ${DATA_DIR:-./data}"
        print_success "Configuration loaded from .env"
    else
        print_error "No .env file found"
        echo "  Run './sheets.sh setup' to configure"
    fi
}

show_help() {
    cat << 'HELPEOF'
📊 DOOMLESS — Groq API Integration Script

USAGE:
    ./sheets.sh <command>

COMMANDS:
    setup       - Configure Groq API key
    export      - Export activity history to JSON
    test        - Test Groq API connection
    config      - Show current configuration
    help        - Show this help message

EXAMPLES:
    ./sheets.sh setup
    ./sheets.sh export
    ./sheets.sh test
    ./sheets.sh config

REQUIREMENTS:
    - curl
    - jq (optional, for pretty JSON)

GROQ API INFO:
    Get your API key at: https://console.groq.com
    Data is stored locally in ./data directory

HELPEOF
}

case "${1:-help}" in
    setup) setup_groq ;;
    export) export_to_json ;;
    test) test_groq_connection ;;
    config) show_config ;;
    help|--help|-h) show_help ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
