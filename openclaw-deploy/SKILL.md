---
name: openclaw-deploy
description: Deploy new OpenClaw instances with full customization. Use when spinning up OpenClaw on Docker (local or remote), bare metal, or VPS. Supports AI provider configuration (primary/fallback, local models via Ollama), channel setup (WhatsApp/Telegram/Discord/Slack/Signal/iMessage), multi-agent routing, sandboxing, and generates human checklists for manual steps (API keys, OAuth, DNS).
---

# OpenClaw Deploy

Deploy fully customized OpenClaw instances anywhere.

## Quick Start

1. Choose deployment target (see [references/targets.md](references/targets.md))
2. Run the deployment script with your config
3. Complete human checklist for manual steps

## Deployment Targets

| Target | Command | Notes |
|--------|---------|-------|
| Docker (local) | `scripts/deploy.sh docker-local` | Fastest for testing |
| Docker (remote) | `scripts/deploy.sh docker-remote --host user@ip` | Production VPS |
| Bare metal | `scripts/deploy.sh bare-metal --host user@ip` | Direct Node.js install |

## Configuration

Generate a deployment config interactively or from a spec file:

```bash
# Interactive
./scripts/deploy.sh configure

# From spec
./scripts/deploy.sh configure --spec deployment-spec.json5
```

### Deployment Spec Schema

```json5
{
  // Target
  target: "docker-local" | "docker-remote" | "bare-metal",
  remoteHost: "user@hostname",  // for remote targets
  sshKey: "~/.ssh/id_ed25519",  // optional

  // AI Configuration
  ai: {
    primary: "anthropic/claude-opus-4-5",
    fallbacks: ["openrouter/anthropic/claude-sonnet-4"],
    
    // Local AI (Ollama)
    local: {
      enabled: false,
      models: ["llama3.3", "qwen2.5-coder:32b"],
      useAsPrimary: false,  // Use local as primary, cloud as fallback
      useAsFallback: true,  // Use local only when cloud fails
    },
  },

  // Channels
  channels: {
    whatsapp: { enabled: true },
    telegram: { enabled: false },
    discord: { enabled: false },
    slack: { enabled: false },
    signal: { enabled: false },
    imessage: { enabled: false },
    webchat: { enabled: true },
  },

  // Agent Identity
  identity: {
    name: "Assistant",
    emoji: "🤖",
    theme: "helpful and concise",
  },

  // Networking
  network: {
    port: 18789,
    domain: null,  // For webhook-based channels
    ssl: false,
  },

  // Sandboxing
  sandbox: {
    enabled: true,
    mode: "non-main",
    scope: "agent",
  },
}
```

## AI Provider Setup

See [references/ai-providers.md](references/ai-providers.md) for:
- Cloud providers (Anthropic, OpenAI, OpenRouter, etc.)
- Local models (Ollama setup and configuration)
- Hybrid setups (local primary, cloud fallback or vice versa)

## Channel Setup

See [references/channels.md](references/channels.md) for per-channel:
- Required credentials
- Setup steps
- Human-required actions

## Human Checklist Generator

After deployment, run:

```bash
./scripts/deploy.sh checklist
```

This generates a markdown checklist of all manual steps:
- API keys to obtain
- OAuth flows to complete
- QR codes to scan
- DNS records to create

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/deploy.sh` | Main deployment orchestrator |
| `scripts/generate-config.py` | Generate openclaw.json5 from spec |
| `scripts/setup-ollama.sh` | Install and configure Ollama |
| `scripts/human-checklist.py` | Generate human action checklist |

## Examples

### Minimal local Docker deployment

```bash
./scripts/deploy.sh docker-local \
  --ai-primary "anthropic/claude-sonnet-4" \
  --channel whatsapp
```

### Production VPS with Ollama fallback

```bash
./scripts/deploy.sh docker-remote \
  --host deploy@myserver.com \
  --ai-primary "anthropic/claude-opus-4-5" \
  --ai-fallback "ollama/llama3.3" \
  --local-ai \
  --channels whatsapp,telegram \
  --domain openclaw.myserver.com \
  --ssl
```

### Local-first with cloud fallback

```bash
./scripts/deploy.sh docker-local \
  --ai-primary "ollama/qwen2.5-coder:32b" \
  --ai-fallback "openrouter/anthropic/claude-sonnet-4" \
  --local-ai
```

## Shared Skill Repository

New agents can contribute to a shared skill repo, so improvements propagate across all instances.

```bash
./scripts/deploy.sh docker-local \
  --skill-repo "github.com/yourorg/openclaw-skills" \
  ...
```

This:
1. Clones the skill repo to `~/.openclaw/workspace/openclaw-skills/`
2. Symlinks skills into `~/.openclaw/skills/`
3. Adds push scripts to the workspace
4. Configures AGENTS.md with contribution instructions

See [references/skill-sharing.md](references/skill-sharing.md) for:
- Setting up a shared skill repo
- Fork vs upstream workflow
- Contribution automation

## Capability Tiers

Control what an agent can access based on trust level:

```bash
./scripts/deploy.sh docker-local \
  --tier standard \
  --ai-primary "anthropic/claude-sonnet-4" \
  --channel telegram
```

| Tier | Trust | Use Case |
|------|-------|----------|
| `minimal` | None | Public bots, demos |
| `standard` | Low | Family, friends (default) |
| `trusted` | Medium | Work, collaborators |
| `full` | High | Personal main agent |

Each tier gets appropriate:
- Workspace files (AGENTS.md, SOUL.md, MEMORY.md, etc.)
- Tool access (sandbox policies)
- Skill allowlists (filter by declared tier)

See [references/capability-tiers.md](references/capability-tiers.md) for full matrix.

## Platform Detection

The deploy script automatically detects:
- OS (macOS, Linux)
- Architecture (x86_64, arm64)
- GPU (NVIDIA, Apple Silicon)
- RAM (for model size recommendations)
- Container environment

And **blocks incompatible combinations**:
- iMessage on Linux → Error
- NVIDIA GPU on macOS → Error
- 70B model with 16GB RAM → Warning

See [references/platform-compat.md](references/platform-compat.md) for compatibility matrix.

## Skill Safety Metadata

Skills should declare requirements in SKILL.md frontmatter:

```yaml
---
name: imsg
platforms:
  - os: darwin
    container: false
permissions:
  - full-disk-access
  - messages-automation
risks:
  - personal-data
  - impersonation
tier: full
---
```

The deploy script filters skills by:
1. Platform compatibility
2. Agent's capability tier
3. Approved risk categories

See [references/skill-metadata.md](references/skill-metadata.md) for schema and examples.

## Reference Files

- [references/targets.md](references/targets.md) — Deployment target details
- [references/ai-providers.md](references/ai-providers.md) — AI provider configuration
- [references/channels.md](references/channels.md) — Channel setup guides
- [references/human-steps.md](references/human-steps.md) — Manual step templates
- [references/skill-sharing.md](references/skill-sharing.md) — Shared skill repository setup
- [references/capability-tiers.md](references/capability-tiers.md) — Capability tier definitions
- [references/platform-compat.md](references/platform-compat.md) — Platform compatibility matrix
- [references/skill-metadata.md](references/skill-metadata.md) — Skill safety metadata schema
