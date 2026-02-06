# AI Provider Configuration

## Cloud Providers

### Anthropic (Claude)

**Models:** claude-opus-4-5, claude-sonnet-4, claude-haiku

**Setup:**
1. Get API key: https://console.anthropic.com/
2. Set env: `ANTHROPIC_API_KEY=sk-ant-...`

**Config:**
```json5
{
  agents: {
    defaults: {
      model: { primary: "anthropic/claude-opus-4-5" }
    }
  }
}
```

**Human Required:** API key from Anthropic Console

---

### OpenAI

**Models:** gpt-4o, gpt-4-turbo, o1, o1-mini

**Setup:**
1. Get API key: https://platform.openai.com/api-keys
2. Set env: `OPENAI_API_KEY=sk-...`

**Config:**
```json5
{
  agents: {
    defaults: {
      model: { primary: "openai/gpt-4o" }
    }
  }
}
```

**Human Required:** API key from OpenAI Platform

---

### OpenRouter (Multi-provider)

Access many providers through one API. Good for fallbacks.

**Setup:**
1. Get API key: https://openrouter.ai/keys
2. Set env: `OPENROUTER_API_KEY=sk-or-...`

**Config:**
```json5
{
  agents: {
    defaults: {
      model: {
        primary: "openrouter/anthropic/claude-opus-4-5",
        fallbacks: ["openrouter/openai/gpt-4o"]
      }
    }
  }
}
```

**Human Required:** API key from OpenRouter

---

### Venice AI (Privacy-focused)

Privacy-first inference with optional Opus access.

**Setup:**
1. Get API key: https://venice.ai/
2. Set env: `VENICE_API_KEY=...`

**Config:**
```json5
{
  agents: {
    defaults: {
      model: { primary: "venice/llama-3.3-70b" }
    }
  }
}
```

---

## Local AI (Ollama)

Run models locally for privacy, cost savings, or offline use.

### Installation

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Docker
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Pull Models

```bash
# General purpose
ollama pull llama3.3
ollama pull qwen2.5-coder:32b

# Reasoning
ollama pull deepseek-r1:32b

# Small/fast
ollama pull llama3.2:3b
ollama pull phi3:mini
```

### OpenClaw Configuration

**Auto-discovery (recommended):**
```bash
export OLLAMA_API_KEY="ollama-local"
```

Models with tool support are auto-discovered.

**Explicit config:**
```json5
{
  models: {
    providers: {
      ollama: {
        baseUrl: "http://localhost:11434/v1",
        apiKey: "ollama-local",
        api: "openai-completions",
        models: [
          {
            id: "llama3.3",
            name: "Llama 3.3",
            reasoning: false,
            input: ["text"],
            cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
            contextWindow: 8192,
            maxTokens: 81920
          }
        ]
      }
    }
  }
}
```

### GPU Acceleration

**macOS (Apple Silicon):**
- Automatic via Metal

**Linux (NVIDIA):**
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Run Ollama with GPU
docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

**Human Required:** GPU drivers if using acceleration

---

## Hybrid Configurations

### Cloud Primary, Local Fallback

Use cloud for best quality, fall back to local when cloud fails:

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "anthropic/claude-opus-4-5",
        fallbacks: ["ollama/llama3.3"]
      }
    }
  }
}
```

### Local Primary, Cloud Fallback

Use local for privacy/cost, fall back to cloud for complex tasks:

```json5
{
  agents: {
    defaults: {
      model: {
        primary: "ollama/qwen2.5-coder:32b",
        fallbacks: ["openrouter/anthropic/claude-sonnet-4"]
      }
    }
  }
}
```

### Per-Agent Model Assignment

Different agents use different models:

```json5
{
  agents: {
    defaults: {
      model: { primary: "ollama/llama3.3" }  // default
    },
    list: [
      {
        id: "main",
        model: { primary: "anthropic/claude-opus-4-5" }  // premium
      },
      {
        id: "family",
        model: { primary: "ollama/llama3.2:3b" }  // lightweight
      }
    ]
  }
}
```

---

## Model Selection Guide

| Use Case | Recommended | Notes |
|----------|-------------|-------|
| Best quality | claude-opus-4-5 | Highest capability |
| Cost-effective | claude-sonnet-4, gpt-4o | Good balance |
| Privacy | ollama/llama3.3 | Fully local |
| Coding | qwen2.5-coder:32b | Code-specialized |
| Fast/cheap | llama3.2:3b, phi3:mini | Quick responses |
| Reasoning | deepseek-r1:32b, o1 | Chain-of-thought |

---

## Environment Variables Summary

```bash
# Cloud providers
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."
export VENICE_API_KEY="..."

# Local
export OLLAMA_API_KEY="ollama-local"

# Alternative: use .env file
# ~/.openclaw/.env
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_API_KEY=ollama-local
```
