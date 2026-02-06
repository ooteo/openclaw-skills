#!/usr/bin/env bash
set -euo pipefail

# Ollama Setup Script for OpenClaw
# Installs Ollama and pulls specified models

MODELS="${1:-llama3.3}"
GPU="${2:-auto}"

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
Ollama Setup Script

USAGE:
    $0 [models] [gpu]

ARGUMENTS:
    models    Comma-separated list of models to pull (default: llama3.3)
    gpu       GPU mode: auto, nvidia, none (default: auto)

EXAMPLES:
    $0
    $0 llama3.3,qwen2.5-coder:32b
    $0 llama3.3 nvidia
    $0 deepseek-r1:32b none

RECOMMENDED MODELS:
    llama3.3              General purpose (8B)
    qwen2.5-coder:32b     Code generation
    deepseek-r1:32b       Reasoning/chain-of-thought
    llama3.2:3b           Fast/lightweight
    phi3:mini             Very small, good for testing

EOF
    exit 1
}

[[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && usage

detect_os() {
    case "$(uname -s)" in
        Darwin) echo "macos" ;;
        Linux) echo "linux" ;;
        *) echo "unknown" ;;
    esac
}

detect_gpu() {
    if [[ "$GPU" != "auto" ]]; then
        echo "$GPU"
        return
    fi
    
    # Check for NVIDIA GPU
    if command -v nvidia-smi &>/dev/null; then
        if nvidia-smi &>/dev/null; then
            echo "nvidia"
            return
        fi
    fi
    
    # macOS Apple Silicon
    if [[ "$(detect_os)" == "macos" ]]; then
        if [[ "$(uname -m)" == "arm64" ]]; then
            echo "metal"
            return
        fi
    fi
    
    echo "none"
}

install_ollama() {
    log_info "Installing Ollama..."
    
    local os=$(detect_os)
    
    case "$os" in
        macos)
            if command -v brew &>/dev/null; then
                brew install ollama
            else
                log_error "Homebrew not found. Install from https://ollama.ai"
                exit 1
            fi
            ;;
        linux)
            curl -fsSL https://ollama.ai/install.sh | sh
            ;;
        *)
            log_error "Unsupported OS. Install manually from https://ollama.ai"
            exit 1
            ;;
    esac
    
    log_success "Ollama installed"
}

setup_nvidia_docker() {
    log_info "Setting up NVIDIA Container Toolkit..."
    
    # Check if already installed
    if docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &>/dev/null; then
        log_success "NVIDIA Container Toolkit already working"
        return
    fi
    
    # Install toolkit
    distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
    curl -s -L "https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list" | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    sudo systemctl restart docker
    
    log_success "NVIDIA Container Toolkit installed"
}

start_ollama() {
    log_info "Starting Ollama..."
    
    local os=$(detect_os)
    local gpu=$(detect_gpu)
    
    if [[ "$os" == "linux" ]]; then
        # Try systemd first
        if systemctl is-active --quiet ollama 2>/dev/null; then
            log_success "Ollama already running (systemd)"
            return
        fi
        
        if systemctl enable ollama 2>/dev/null && systemctl start ollama 2>/dev/null; then
            log_success "Ollama started via systemd"
            return
        fi
    fi
    
    # Fallback: start in background
    if pgrep -x ollama &>/dev/null; then
        log_success "Ollama already running"
        return
    fi
    
    ollama serve &>/dev/null &
    sleep 3
    
    if pgrep -x ollama &>/dev/null; then
        log_success "Ollama started (background)"
    else
        log_error "Failed to start Ollama"
        exit 1
    fi
}

pull_models() {
    log_info "Pulling models: $MODELS"
    
    IFS=',' read -ra MODEL_LIST <<< "$MODELS"
    
    for model in "${MODEL_LIST[@]}"; do
        model=$(echo "$model" | xargs)  # trim whitespace
        log_info "Pulling: $model"
        
        if ollama pull "$model"; then
            log_success "Pulled: $model"
        else
            log_error "Failed to pull: $model"
        fi
    done
}

verify_setup() {
    log_info "Verifying Ollama setup..."
    
    # Check Ollama is running
    if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
        log_error "Ollama not responding on localhost:11434"
        exit 1
    fi
    
    # List models
    log_info "Installed models:"
    ollama list
    
    # GPU info
    local gpu=$(detect_gpu)
    log_info "GPU acceleration: $gpu"
    
    log_success "Ollama setup complete!"
    
    echo ""
    echo "Add to your OpenClaw .env:"
    echo "  OLLAMA_API_KEY=ollama-local"
    echo ""
    echo "Use models like:"
    IFS=',' read -ra MODEL_LIST <<< "$MODELS"
    for model in "${MODEL_LIST[@]}"; do
        model=$(echo "$model" | xargs)
        echo "  ollama/$model"
    done
}

main() {
    local gpu=$(detect_gpu)
    
    log_info "Detected GPU: $gpu"
    
    # Install Ollama if needed
    if ! command -v ollama &>/dev/null; then
        install_ollama
    else
        log_success "Ollama already installed"
    fi
    
    # Setup NVIDIA Docker if needed
    if [[ "$gpu" == "nvidia" ]] && [[ "$(detect_os)" == "linux" ]]; then
        setup_nvidia_docker
    fi
    
    # Start Ollama
    start_ollama
    
    # Pull models
    pull_models
    
    # Verify
    verify_setup
}

main
