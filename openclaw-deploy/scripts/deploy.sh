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

#######################################
# Platform Detection
#######################################
detect_platform() {
    PLATFORM_OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    PLATFORM_ARCH=$(uname -m)
    PLATFORM_CONTAINER=""
    PLATFORM_GPU=""
    PLATFORM_PKG=""
    
    # Normalize OS
    case "$PLATFORM_OS" in
        darwin) PLATFORM_OS="darwin" ;;
        linux) PLATFORM_OS="linux" ;;
        *) PLATFORM_OS="unknown" ;;
    esac
    
    # Normalize arch
    case "$PLATFORM_ARCH" in
        x86_64|amd64) PLATFORM_ARCH="x86_64" ;;
        arm64|aarch64) PLATFORM_ARCH="arm64" ;;
    esac
    
    # Detect container
    if [[ -f /proc/1/cgroup ]] && grep -q docker /proc/1/cgroup 2>/dev/null; then
        PLATFORM_CONTAINER="docker"
    elif [[ -f /.dockerenv ]]; then
        PLATFORM_CONTAINER="docker"
    fi
    
    # Detect GPU
    if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null; then
        PLATFORM_GPU="nvidia"
    elif [[ "$PLATFORM_OS" == "darwin" && "$PLATFORM_ARCH" == "arm64" ]]; then
        PLATFORM_GPU="apple"
    fi
    
    # Detect package manager
    if command -v brew &>/dev/null; then
        PLATFORM_PKG="brew"
    elif command -v apt-get &>/dev/null; then
        PLATFORM_PKG="apt"
    elif command -v dnf &>/dev/null; then
        PLATFORM_PKG="dnf"
    elif command -v apk &>/dev/null; then
        PLATFORM_PKG="apk"
    elif command -v pacman &>/dev/null; then
        PLATFORM_PKG="pacman"
    fi
    
    # Get RAM (in GB)
    if [[ "$PLATFORM_OS" == "darwin" ]]; then
        PLATFORM_RAM=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
    elif [[ -f /proc/meminfo ]]; then
        PLATFORM_RAM=$(($(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024))
    else
        PLATFORM_RAM=0
    fi
}

validate_platform_compat() {
    local errors=()
    local warnings=()
    
    # Check iMessage
    if [[ "$CHANNELS" == *"imessage"* && "$PLATFORM_OS" != "darwin" ]]; then
        errors+=("iMessage requires macOS (detected: $PLATFORM_OS)")
    fi
    
    # Check NVIDIA GPU on macOS
    if [[ "$LOCAL_AI" == "true" && "$PLATFORM_GPU" == "nvidia" && "$PLATFORM_OS" == "darwin" ]]; then
        errors+=("NVIDIA GPU not supported on macOS")
    fi
    
    # Check container + Apple Silicon GPU
    if [[ "$LOCAL_AI" == "true" && -n "$PLATFORM_CONTAINER" && "$PLATFORM_GPU" == "apple" ]]; then
        warnings+=("Apple Silicon GPU not available in containers - will use CPU")
    fi
    
    # Check RAM for large models
    if [[ "$LOCAL_AI" == "true" ]]; then
        if [[ "$LOCAL_MODELS" == *"70b"* && "$PLATFORM_RAM" -lt 64 ]]; then
            warnings+=("70B models recommend 64GB+ RAM (detected: ${PLATFORM_RAM}GB)")
        elif [[ "$LOCAL_MODELS" == *"32b"* && "$PLATFORM_RAM" -lt 32 ]]; then
            warnings+=("32B models recommend 32GB+ RAM (detected: ${PLATFORM_RAM}GB)")
        fi
    fi
    
    # Print warnings
    for warn in "${warnings[@]}"; do
        log_warn "$warn"
    done
    
    # Print errors and exit if any
    if [[ ${#errors[@]} -gt 0 ]]; then
        for err in "${errors[@]}"; do
            log_error "$err"
        done
        exit 1
    fi
}

print_platform_info() {
    log_info "Platform detected:"
    log_info "  OS: $PLATFORM_OS"
    log_info "  Arch: $PLATFORM_ARCH"
    log_info "  RAM: ${PLATFORM_RAM}GB"
    [[ -n "$PLATFORM_GPU" ]] && log_info "  GPU: $PLATFORM_GPU"
    [[ -n "$PLATFORM_PKG" ]] && log_info "  Package manager: $PLATFORM_PKG"
    [[ -n "$PLATFORM_CONTAINER" ]] && log_info "  Container: $PLATFORM_CONTAINER"
}

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
    --skill-repo <url>      Shared skill repository (e.g., github.com/yourorg/skills)
    --tier <level>          Capability tier (minimal|standard|trusted|full, default: standard)
    --name <name>           Agent name (default: Assistant)
    --pronouns <pronouns>   Agent pronouns (she/her, he/him, they/them, etc.)
    --emoji <emoji>         Agent emoji (default: 🤖)
    --theme <desc>          Personality theme/description
    --creator <name>        Creator name (default: current user)
    --parent-agent <guid>   Parent agent GUID (if spawned by another agent)
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
SKILL_REPO=""
TIER="standard"
AGENT_NAME="Assistant"
AGENT_PRONOUNS=""
AGENT_EMOJI="🤖"
AGENT_THEME=""
AGENT_CREATOR="${USER:-$(whoami)}"
PARENT_AGENT=""
AGENT_GUID=""
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
        --skill-repo)
            SKILL_REPO="$2"
            shift 2
            ;;
        --tier)
            TIER="$2"
            if [[ ! "$TIER" =~ ^(minimal|standard|trusted|full)$ ]]; then
                log_error "Invalid tier: $TIER (must be minimal|standard|trusted|full)"
                exit 1
            fi
            shift 2
            ;;
        --name)
            AGENT_NAME="$2"
            shift 2
            ;;
        --pronouns)
            AGENT_PRONOUNS="$2"
            shift 2
            ;;
        --emoji)
            AGENT_EMOJI="$2"
            shift 2
            ;;
        --theme)
            AGENT_THEME="$2"
            shift 2
            ;;
        --creator)
            AGENT_CREATOR="$2"
            shift 2
            ;;
        --parent-agent)
            PARENT_AGENT="$2"
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
    
    # Detect and validate platform
    detect_platform
    print_platform_info
    validate_platform_compat
    
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
    
    # Setup skill sharing if configured
    if [[ -n "$SKILL_REPO" ]]; then
        setup_skill_sharing_local
    fi
    
    # Setup workspace templates
    setup_workspace_templates_local
    
    log_success "Local Docker deployment complete!"
    log_info "Access Control UI at: http://127.0.0.1:$PORT"
    log_info "Capability tier: $TIER"
    
    # Generate checklist
    generate_checklist
}

#######################################
# Docker Remote Deployment
#######################################
deploy_docker_remote() {
    log_info "Deploying OpenClaw to remote Docker host: $HOST"
    
    [[ -z "$HOST" ]] && { log_error "--host required for docker-remote"; exit 1; }
    
    # Detect local platform for validation (remote will be Linux typically)
    detect_platform
    validate_platform_compat
    
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
    
    # Setup skill sharing if configured
    if [[ -n "$SKILL_REPO" ]]; then
        setup_skill_sharing_remote
    fi
    
    # Setup workspace templates
    setup_workspace_templates_remote
    
    log_success "Remote Docker deployment complete!"
    log_info "Capability tier: $TIER"
    
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
    # Detect and validate platform
    detect_platform
    print_platform_info
    validate_platform_compat
    
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
    
    # Setup skill sharing if configured
    if [[ -n "$SKILL_REPO" ]]; then
        setup_skill_sharing_local
    fi
    
    # Setup workspace templates
    setup_workspace_templates_local
    
    log_success "Bare metal deployment complete!"
    log_info "Capability tier: $TIER"
    log_info "Start gateway with: openclaw gateway start"
    
    # Generate checklist
    generate_checklist
}

deploy_bare_metal_remote() {
    [[ -z "$HOST" ]] && { log_error "--host required"; exit 1; }
    
    # Detect local platform for validation
    detect_platform
    validate_platform_compat
    
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
    
    # Setup skill sharing if configured
    if [[ -n "$SKILL_REPO" ]]; then
        setup_skill_sharing_remote
    fi
    
    # Setup workspace templates
    setup_workspace_templates_remote
    
    log_success "Remote bare metal deployment complete!"
    log_info "Capability tier: $TIER"
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
# Skill Sharing Setup
#######################################
setup_skill_sharing_local() {
    [[ -z "$SKILL_REPO" ]] && return
    
    log_info "Setting up shared skill repository..."
    
    local repo_url="https://$SKILL_REPO"
    local repo_dir="$HOME/.openclaw/workspace/openclaw-skills"
    local scripts_dir="$HOME/.openclaw/workspace/scripts"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would clone $repo_url to $repo_dir"
        return
    fi
    
    # Clone repo
    if [[ ! -d "$repo_dir" ]]; then
        git clone "$repo_url" "$repo_dir"
    else
        log_info "Skill repo already exists, pulling latest..."
        cd "$repo_dir" && git pull
    fi
    
    # Create scripts directory
    mkdir -p "$scripts_dir"
    
    # Create push-skill.sh
    cat > "$scripts_dir/push-skill.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
SKILL_NAME="$1"
SKILL_SRC="$HOME/.openclaw/skills/$SKILL_NAME"
REPO_DIR="$HOME/.openclaw/workspace/openclaw-skills"
[[ ! -d "$SKILL_SRC" ]] && { echo "Skill not found: $SKILL_SRC" >&2; exit 1; }
echo "Copying $SKILL_NAME to repo..."
rm -rf "$REPO_DIR/$SKILL_NAME"
cp -r "$SKILL_SRC" "$REPO_DIR/$SKILL_NAME"
cd "$REPO_DIR"
git add "$SKILL_NAME"
git commit -m "Update skill: $SKILL_NAME" || echo "No changes to commit"
git push
echo "✓ Pushed $SKILL_NAME to GitHub"
SCRIPT
    chmod +x "$scripts_dir/push-skill.sh"
    
    # Create push-all-skills.sh
    cat > "$scripts_dir/push-all-skills.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
SKILLS_DIR="$HOME/.openclaw/skills"
REPO_DIR="$HOME/.openclaw/workspace/openclaw-skills"
cd "$REPO_DIR"
for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    [[ -f "$skill_dir/SKILL.md" ]] || continue
    echo "Syncing: $skill_name"
    rm -rf "$REPO_DIR/$skill_name"
    cp -r "$skill_dir" "$REPO_DIR/$skill_name"
done
git add -A
git commit -m "Sync all skills: $(date +%Y-%m-%d)" || echo "No changes"
git push
echo "✓ All skills pushed"
SCRIPT
    chmod +x "$scripts_dir/push-all-skills.sh"
    
    # Sync existing skills from repo
    log_info "Syncing skills from repo..."
    for skill_dir in "$repo_dir"/*/; do
        local skill_name=$(basename "$skill_dir")
        [[ -f "$skill_dir/SKILL.md" ]] || continue
        if [[ ! -d "$HOME/.openclaw/skills/$skill_name" ]]; then
            log_info "Installing skill: $skill_name"
            cp -r "$skill_dir" "$HOME/.openclaw/skills/$skill_name"
        fi
    done
    
    log_success "Skill sharing configured: $SKILL_REPO"
}

setup_skill_sharing_remote() {
    [[ -z "$SKILL_REPO" ]] && return
    
    log_info "Setting up shared skill repository on remote..."
    
    SSH_CMD="ssh"
    [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would setup skill repo on $HOST"
        return
    fi
    
    $SSH_CMD "$HOST" bash <<REMOTE_SCRIPT
SKILL_REPO="$SKILL_REPO"
REPO_URL="https://\$SKILL_REPO"
REPO_DIR="\$HOME/.openclaw/workspace/openclaw-skills"
SCRIPTS_DIR="\$HOME/.openclaw/workspace/scripts"

# Clone repo
mkdir -p "\$HOME/.openclaw/workspace"
if [[ ! -d "\$REPO_DIR" ]]; then
    git clone "\$REPO_URL" "\$REPO_DIR"
fi

# Create scripts
mkdir -p "\$SCRIPTS_DIR"

cat > "\$SCRIPTS_DIR/push-skill.sh" <<'INNERSCRIPT'
#!/usr/bin/env bash
set -euo pipefail
SKILL_NAME="\$1"
SKILL_SRC="\$HOME/.openclaw/skills/\$SKILL_NAME"
REPO_DIR="\$HOME/.openclaw/workspace/openclaw-skills"
[[ ! -d "\$SKILL_SRC" ]] && { echo "Skill not found: \$SKILL_SRC" >&2; exit 1; }
rm -rf "\$REPO_DIR/\$SKILL_NAME"
cp -r "\$SKILL_SRC" "\$REPO_DIR/\$SKILL_NAME"
cd "\$REPO_DIR"
git add "\$SKILL_NAME"
git commit -m "Update skill: \$SKILL_NAME" || true
git push
INNERSCRIPT
chmod +x "\$SCRIPTS_DIR/push-skill.sh"

# Sync skills from repo
mkdir -p "\$HOME/.openclaw/skills"
for skill_dir in "\$REPO_DIR"/*/; do
    skill_name=\$(basename "\$skill_dir")
    [[ -f "\$skill_dir/SKILL.md" ]] || continue
    [[ ! -d "\$HOME/.openclaw/skills/\$skill_name" ]] && cp -r "\$skill_dir" "\$HOME/.openclaw/skills/\$skill_name"
done
REMOTE_SCRIPT
    
    log_success "Remote skill sharing configured"
}

#######################################
# GUID Generation
#######################################
generate_agent_guid() {
    if [[ -z "$AGENT_GUID" ]]; then
        AGENT_GUID="agt_$(openssl rand -hex 8)"
    fi
    echo "$AGENT_GUID"
}

#######################################
# Identity File Generation
#######################################
generate_identity_file() {
    local output_file="$1"
    local guid=$(generate_agent_guid)
    local created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local generation=0
    local creator_type="human"
    
    if [[ -n "$PARENT_AGENT" ]]; then
        creator_type="agent"
        generation=1  # Would need to query parent for actual generation
    fi
    
    cat > "$output_file" << EOF
# IDENTITY.md - Who Am I?

## Core
- **GUID:** $guid
- **Name:** $AGENT_NAME
${AGENT_PRONOUNS:+- **Pronouns:** $AGENT_PRONOUNS}
- **Emoji:** $AGENT_EMOJI

## Personality
${AGENT_THEME:-A helpful AI assistant.}

## Lineage
- **Created:** $created_at
- **Creator:** $AGENT_CREATOR ($creator_type)
- **Generation:** $generation
${PARENT_AGENT:+- **Parent Agent:** $PARENT_AGENT}

## Relationships

### Trusted
${PARENT_AGENT:+- $PARENT_AGENT (parent)}

### Blocked
(none)

---

Born $created_at. Identity established at deployment.
EOF
    
    log_info "Generated IDENTITY.md (GUID: $guid)"
}

#######################################
# Workspace Templates Setup
#######################################
setup_workspace_templates_local() {
    log_info "Setting up workspace templates (tier: $TIER)..."
    
    local workspace_dir="$HOME/.openclaw/workspace"
    local templates_dir="$SKILL_DIR/assets/templates/$TIER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would copy $TIER templates to $workspace_dir"
        return
    fi
    
    mkdir -p "$workspace_dir"
    mkdir -p "$workspace_dir/memory"
    
    # Copy templates (don't overwrite existing files)
    for template_file in "$templates_dir"/*; do
        local filename=$(basename "$template_file")
        local target="$workspace_dir/$filename"
        
        # Skip IDENTITY.md - we generate it custom
        if [[ "$filename" == "IDENTITY.md" ]]; then
            continue
        fi
        
        if [[ ! -f "$target" ]]; then
            cp "$template_file" "$target"
            log_info "Created: $filename"
        else
            log_info "Skipped (exists): $filename"
        fi
    done
    
    # Generate custom IDENTITY.md
    if [[ ! -f "$workspace_dir/IDENTITY.md" ]]; then
        generate_identity_file "$workspace_dir/IDENTITY.md"
    else
        log_info "Skipped (exists): IDENTITY.md"
    fi
    
    log_success "Workspace templates installed for $TIER tier"
}

setup_workspace_templates_remote() {
    log_info "Setting up workspace templates on remote (tier: $TIER)..."
    
    SSH_CMD="ssh"
    [[ -n "$SSH_KEY" ]] && SSH_CMD="ssh -i $SSH_KEY"
    
    local templates_dir="$SKILL_DIR/assets/templates/$TIER"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would copy $TIER templates to remote"
        return
    fi
    
    # Create workspace on remote
    $SSH_CMD "$HOST" "mkdir -p ~/.openclaw/workspace/memory"
    
    # Copy each template file (except IDENTITY.md)
    for template_file in "$templates_dir"/*; do
        local filename=$(basename "$template_file")
        
        # Skip IDENTITY.md - we generate it custom
        if [[ "$filename" == "IDENTITY.md" ]]; then
            continue
        fi
        
        # Check if file exists on remote before copying
        if ! $SSH_CMD "$HOST" "test -f ~/.openclaw/workspace/$filename"; then
            scp ${SSH_KEY:+-i "$SSH_KEY"} "$template_file" "$HOST:~/.openclaw/workspace/$filename"
            log_info "Created: $filename"
        else
            log_info "Skipped (exists): $filename"
        fi
    done
    
    # Generate custom IDENTITY.md locally then copy
    if ! $SSH_CMD "$HOST" "test -f ~/.openclaw/workspace/IDENTITY.md"; then
        local temp_identity=$(mktemp)
        generate_identity_file "$temp_identity"
        scp ${SSH_KEY:+-i "$SSH_KEY"} "$temp_identity" "$HOST:~/.openclaw/workspace/IDENTITY.md"
        rm "$temp_identity"
    else
        log_info "Skipped (exists): IDENTITY.md"
    fi
    
    log_success "Remote workspace templates installed for $TIER tier"
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
