#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Deploy Script
# Usage: ./deploy.sh <command> [options]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

usage() {
    cat <<EOF
OpenClaw Deploy Script

USAGE:
    $0 <command> [options]

COMMANDS:
    docker-local    Deploy to local Docker
    docker-remote   Deploy to remote Docker host
    bare-metal      Deploy directly via Node.js
    configure       Generate deployment configuration
    checklist       Generate human action checklist
    status          Check deployment status

OPTIONS:
    --host <user@ip>        Remote host for docker-remote/bare-metal
    --ssh-key <path>        SSH key for remote connections
    --ai-primary <model>    Primary AI model (e.g., anthropic/claude-opus-4-5)
    --ai-fallback <model>   Fallback AI model(s), comma-separated
    --local-ai              Enable Ollama for local AI
    --local-models <list>   Ollama models to pull, comma-separated
    --channel <name>        Enable channel (whatsapp,telegram,discord,slack,signal,imessage)
    --channels <list>       Enable multiple channels, comma-separated
    --domain <domain>       Domain for webhooks/SSL
    --port <port>           Gateway port (default: 18789)
    --ssl                   Enable SSL (requires domain)
    --spec <file>           Load configuration from spec file
    --output <dir>          Output directory for generated files
    --dry-run               Show what would be done without executing

EXAMPLES:
    # Local Docker with WhatsApp
    $0 docker-local --channel whatsapp --ai-primary anthropic/claude-sonnet-4

    # Remote VPS with Ollama fallback
    $0 docker-remote --host deploy@vps.com --ai-primary anthropic/claude-opus-4-5 \\
        --ai-fallback ollama/llama3.3 --local-ai --channels whatsapp,telegram

    # Generate checklist only
    $0 checklist --spec my-deployment.json5

EOF
    exit 1
}

# Parse arguments
COMMAND=""
HOST=""
SSH_KEY=""
AI_PRIMARY=""
AI_FALLBACK=""
LOCAL_AI=false
LOCAL_MODELS="llama3.3"
CHANNELS=""
DOMAIN=""
PORT=18789
SSL=false
SPEC_FILE=""
OUTPUT_DIR=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        docker-local|docker-remote|bare-metal|configure|checklist|status)
            COMMAND="$1"
            shift
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        --ai-primary)
            AI_PRIMARY="$2"
            shift 2
            ;;
        --ai-fallback)
            AI_FALLBACK="$2"
            shift 2
            ;;
        --local-ai)
            LOCAL_AI=true
            shift
            ;;
        --local-models)
            LOCAL_MODELS="$2"
            shift 2
            ;;
        --channel)
            CHANNELS="$2"
            shift 2
            ;;
        --channels)
            CHANNELS="$2"
            shift 2
            ;;
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --ssl)
            SSL=true
            shift
            ;;
        --spec)
            SPEC_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

[[ -z "$COMMAND" ]] && usage

# Set output directory
OUTPUT_DIR="${OUTPUT_DIR:-$(pwd)/openclaw-deploy}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

#######################################
# Docker Local Deployment
#######################################
deploy_docker_local() {
    log_info "Deploying OpenClaw to local Docker..."
    
    # Check Docker
    if ! command -v docker &>/dev/null; then
        log_error "Docker not found. Install Docker first."
        exit 1
    fi
    
    # Generate config
    generate_config
    
    # Clone/update OpenClaw
    if [[ ! -d "$OUTPUT_DIR/openclaw" ]]; then
        log_info "Cloning OpenClaw..."
        if [[ "$DRY_RUN" == "false" ]]; then
            git clone https://github.com/openclaw/openclaw.git "$OUTPUT_DIR/openclaw"
        else
            log_info "[DRY-RUN] Would clone OpenClaw repo"
        fi
    fi
    
    # Copy config
    log_info "Copying configuration..."
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p ~/.openclaw
        cp "$OUTPUT_DIR/openclaw.json5" ~/.openclaw/openclaw.json
    else
        log_info "[DRY-RUN] Would copy config to ~/.openclaw/"
    fi
    
    # Setup Ollama if enabled
    if [[ "$LOCAL_AI" == "true" ]]; then
        setup_ollama_local
    fi
    
    # Run Docker setup
    log_info "Running Docker setup..."
    if [[ "$DRY_RUN" == "false" ]]; then
        cd "$OUTPUT_DIR/openclaw"
        ./docker-setup.sh
    else
        log_info "[DRY-RUN] Would run docker-setup.sh"
    fi
    
    log_success "Local Docker deployment complete!"
    log_info "Access Control UI at: http://127.0.0.1:$PORT"
    
    # Generate checklist
    generate_checklist
}

#######################################
# Docker Remote Deployment
#######################################
deploy_docker_remote() {
    log_info "Deploying OpenClaw to remote Docker host: $HOST"
    
    [[ -z "$HOST" ]] && { log_error "--host required for docker-remote"; exit 1; }
    
    # Build SSH command
    SSH_CMD="ssh"
    [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
    
    # Generate config locally
    generate_config
    
    # Check remote Docker
    log_info "Checking remote Docker..."
    if [[ "$DRY_RUN" == "false" ]]; then
        if ! $SSH_CMD "$HOST" "docker --version" &>/dev/null; then
            log_warn "Docker not found on remote. Installing..."
            $SSH_CMD "$HOST" "curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker \$USER"
            log_info "Docker installed. You may need to reconnect for group changes."
        fi
    else
        log_info "[DRY-RUN] Would check/install Docker on $HOST"
    fi
    
    # Create remote directories
    log_info "Creating remote directories..."
    if [[ "$DRY_RUN" == "false" ]]; then
        $SSH_CMD "$HOST" "mkdir -p ~/.openclaw ~/openclaw-deploy"
    else
        log_info "[DRY-RUN] Would create directories on $HOST"
    fi
    
    # Copy config to remote
    log_info "Copying configuration to remote..."
    if [[ "$DRY_RUN" == "false" ]]; then
        scp ${SSH_KEY:+-i "$SSH_KEY"} "$OUTPUT_DIR/openclaw.json5" "$HOST:~/.openclaw/openclaw.json"
        scp ${SSH_KEY:+-i "$SSH_KEY"} "$OUTPUT_DIR/.env" "$HOST:~/.openclaw/.env" 2>/dev/null || true
    else
        log_info "[DRY-RUN] Would copy config files to $HOST"
    fi
    
    # Clone and setup on remote
    log_info "Setting up OpenClaw on remote..."
    if [[ "$DRY_RUN" == "false" ]]; then
        $SSH_CMD "$HOST" bash <<'REMOTE_SCRIPT'
cd ~/openclaw-deploy
if [[ ! -d openclaw ]]; then
    git clone https://github.com/openclaw/openclaw.git
fi
cd openclaw
git pull
./docker-setup.sh
REMOTE_SCRIPT
    else
        log_info "[DRY-RUN] Would clone and run docker-setup.sh on $HOST"
    fi
    
    # Setup Ollama if enabled
    if [[ "$LOCAL_AI" == "true" ]]; then
        setup_ollama_remote
    fi
    
    log_success "Remote Docker deployment complete!"
    
    if [[ -n "$DOMAIN" ]]; then
        log_info "Access Control UI at: https://$DOMAIN"
    else
        log_info "Access Control UI at: http://<server-ip>:$PORT"
    fi
    
    # Generate checklist
    generate_checklist
}

#######################################
# Bare Metal Deployment
#######################################
deploy_bare_metal() {
    log_info "Deploying OpenClaw via bare metal (Node.js)..."
    
    if [[ -n "$HOST" ]]; then
        deploy_bare_metal_remote
    else
        deploy_bare_metal_local
    fi
}

deploy_bare_metal_local() {
    # Check Node.js
    if ! command -v node &>/dev/null; then
        log_error "Node.js not found. Install Node.js 22+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [[ "$NODE_VERSION" -lt 22 ]]; then
        log_warn "Node.js version $NODE_VERSION found. Version 22+ recommended."
    fi
    
    # Generate config
    generate_config
    
    # Copy config
    log_info "Installing configuration..."
    if [[ "$DRY_RUN" == "false" ]]; then
        mkdir -p ~/.openclaw
        cp "$OUTPUT_DIR/openclaw.json5" ~/.openclaw/openclaw.json
        cp "$OUTPUT_DIR/.env" ~/.openclaw/.env 2>/dev/null || true
    else
        log_info "[DRY-RUN] Would copy config to ~/.openclaw/"
    fi
    
    # Install OpenClaw
    log_info "Installing OpenClaw..."
    if [[ "$DRY_RUN" == "false" ]]; then
        npm install -g openclaw
    else
        log_info "[DRY-RUN] Would run: npm install -g openclaw"
    fi
    
    # Setup Ollama if enabled
    if [[ "$LOCAL_AI" == "true" ]]; then
        setup_ollama_local
    fi
    
    # Run onboarding
    log_info "Running onboarding..."
    if [[ "$DRY_RUN" == "false" ]]; then
        openclaw onboard
    else
        log_info "[DRY-RUN] Would run: openclaw onboard"
    fi
    
    log_success "Bare metal deployment complete!"
    log_info "Start gateway with: openclaw gateway start"
    
    # Generate checklist
    generate_checklist
}

deploy_bare_metal_remote() {
    [[ -z "$HOST" ]] && { log_error "--host required"; exit 1; }
    
    SSH_CMD="ssh"
    [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
    
    # Generate config locally
    generate_config
    
    # Copy config to remote
    log_info "Copying configuration to remote..."
    if [[ "$DRY_RUN" == "false" ]]; then
        $SSH_CMD "$HOST" "mkdir -p ~/.openclaw"
        scp ${SSH_KEY:+-i "$SSH_KEY"} "$OUTPUT_DIR/openclaw.json5" "$HOST:~/.openclaw/openclaw.json"
        scp ${SSH_KEY:+-i "$SSH_KEY"} "$OUTPUT_DIR/.env" "$HOST:~/.openclaw/.env" 2>/dev/null || true
    else
        log_info "[DRY-RUN] Would copy config to $HOST"
    fi
    
    # Install on remote
    log_info "Installing OpenClaw on remote..."
    if [[ "$DRY_RUN" == "false" ]]; then
        $SSH_CMD "$HOST" bash <<'REMOTE_SCRIPT'
# Install Node.js if needed
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
npm install -g openclaw
openclaw onboard
REMOTE_SCRIPT
    else
        log_info "[DRY-RUN] Would install Node.js and OpenClaw on $HOST"
    fi
    
    if [[ "$LOCAL_AI" == "true" ]]; then
        setup_ollama_remote
    fi
    
    log_success "Remote bare metal deployment complete!"
    generate_checklist
}

#######################################
# Ollama Setup
#######################################
setup_ollama_local() {
    log_info "Setting up Ollama locally..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would install Ollama and pull models: $LOCAL_MODELS"
        return
    fi
    
    # Install Ollama
    if ! command -v ollama &>/dev/null; then
        if [[ "$(uname)" == "Darwin" ]]; then
            brew install ollama
        else
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    fi
    
    # Start Ollama
    ollama serve &>/dev/null &
    sleep 2
    
    # Pull models
    IFS=',' read -ra MODELS <<< "$LOCAL_MODELS"
    for model in "${MODELS[@]}"; do
        log_info "Pulling model: $model"
        ollama pull "$model"
    done
    
    log_success "Ollama setup complete"
}

setup_ollama_remote() {
    log_info "Setting up Ollama on remote..."
    
    SSH_CMD="ssh"
    [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would install Ollama on $HOST and pull: $LOCAL_MODELS"
        return
    fi
    
    $SSH_CMD "$HOST" bash <<REMOTE_SCRIPT
# Install Ollama
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service
sudo systemctl enable ollama 2>/dev/null || ollama serve &

# Pull models
sleep 2
for model in ${LOCAL_MODELS//,/ }; do
    ollama pull "\$model"
done
REMOTE_SCRIPT
    
    log_success "Remote Ollama setup complete"
}

#######################################
# Config Generation
#######################################
generate_config() {
    log_info "Generating OpenClaw configuration..."
    
    # Use Python script for complex config generation
    python3 "$SCRIPT_DIR/generate-config.py" \
        --output "$OUTPUT_DIR/openclaw.json5" \
        --env-output "$OUTPUT_DIR/.env" \
        ${AI_PRIMARY:+--ai-primary "$AI_PRIMARY"} \
        ${AI_FALLBACK:+--ai-fallback "$AI_FALLBACK"} \
        ${LOCAL_AI:+--local-ai} \
        ${LOCAL_MODELS:+--local-models "$LOCAL_MODELS"} \
        ${CHANNELS:+--channels "$CHANNELS"} \
        ${DOMAIN:+--domain "$DOMAIN"} \
        --port "$PORT" \
        ${SSL:+--ssl} \
        ${SPEC_FILE:+--spec "$SPEC_FILE"}
    
    log_success "Configuration generated: $OUTPUT_DIR/openclaw.json5"
}

#######################################
# Checklist Generation
#######################################
generate_checklist() {
    log_info "Generating human action checklist..."
    
    python3 "$SCRIPT_DIR/human-checklist.py" \
        --config "$OUTPUT_DIR/openclaw.json5" \
        --output "$OUTPUT_DIR/CHECKLIST.md" \
        ${HOST:+--host "$HOST"} \
        ${DOMAIN:+--domain "$DOMAIN"} \
        --port "$PORT" \
        ${SSL:+--ssl}
    
    log_success "Checklist generated: $OUTPUT_DIR/CHECKLIST.md"
    log_info "Review and complete the checklist before using OpenClaw."
}

#######################################
# Status Check
#######################################
check_status() {
    log_info "Checking deployment status..."
    
    if [[ -n "$HOST" ]]; then
        SSH_CMD="ssh"
        [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
        $SSH_CMD "$HOST" "openclaw status" 2>/dev/null || \
            $SSH_CMD "$HOST" "docker compose -f ~/openclaw-deploy/openclaw/docker-compose.yml ps" 2>/dev/null || \
            log_error "Could not determine status on $HOST"
    else
        openclaw status 2>/dev/null || \
            docker compose ps 2>/dev/null || \
            log_error "OpenClaw not running locally"
    fi
}

#######################################
# Main
#######################################
case "$COMMAND" in
    docker-local)
        deploy_docker_local
        ;;
    docker-remote)
        deploy_docker_remote
        ;;
    bare-metal)
        deploy_bare_metal
        ;;
    configure)
        generate_config
        ;;
    checklist)
        generate_checklist
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac
