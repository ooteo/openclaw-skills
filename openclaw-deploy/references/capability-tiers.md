# Capability Tiers

Control what an agent can access based on trust level and use case.

## Tier Overview

| Tier | Trust | Use Case | Risk Level |
|------|-------|----------|------------|
| `minimal` | None | Public bots, demos, untrusted users | Lowest |
| `standard` | Low | Family, friends, casual use | Low |
| `trusted` | Medium | Work, collaborators, semi-autonomous | Medium |
| `full` | High | Personal main agent, full autonomy | Highest |

## Tier Capabilities Matrix

| Capability | minimal | standard | trusted | full |
|------------|---------|----------|---------|------|
| **Channels** |
| Webchat | ✓ | ✓ | ✓ | ✓ |
| Telegram | - | ✓ | ✓ | ✓ |
| Discord | - | ✓ | ✓ | ✓ |
| WhatsApp | - | - | ✓ | ✓ |
| Signal | - | - | ✓ | ✓ |
| iMessage | - | - | - | ✓ |
| Slack | - | - | ✓ | ✓ |
| **Memory** |
| Session history | ✓ | ✓ | ✓ | ✓ |
| Daily logs | - | ✓ | ✓ | ✓ |
| Long-term (MEMORY.md) | - | - | ✓ | ✓ |
| **Tools** |
| read/write/edit | sandbox | sandbox | workspace | full |
| exec/process | deny | sandbox | workspace | full |
| web_search | ✓ | ✓ | ✓ | ✓ |
| web_fetch | ✓ | ✓ | ✓ | ✓ |
| browser | - | - | sandbox | full |
| cron | - | ✓ | ✓ | ✓ |
| message (cross-channel) | - | - | ✓ | ✓ |
| gateway (config/restart) | - | - | - | ✓ |
| nodes (device control) | - | - | - | ✓ |
| **Skills** |
| Receive from shared repo | ✓ | ✓ | ✓ | ✓ |
| Contribute to shared repo | - | - | ✓ | ✓ |
| Create new skills | - | - | ✓ | ✓ |
| **External Services** |
| Email (send) | - | - | - | ✓ |
| Email (read) | - | - | ✓ | ✓ |
| Social media (read) | - | ✓ | ✓ | ✓ |
| Social media (post) | - | - | - | ✓ |
| Financial (view) | - | - | - | ✓ |
| Financial (transact) | - | - | - | ✓* |
| **System** |
| UI automation | - | - | - | ✓ |
| Elevated commands | - | - | - | ✓ |
| Camera/screen capture | - | - | - | ✓ |

*Financial transactions should always require human confirmation, even at `full` tier.

## Deployment Spec

```json5
{
  capabilities: {
    // Use a preset tier
    tier: "standard",
    
    // Or customize (overrides tier defaults)
    overrides: {
      memory: { longTerm: true },      // Enable MEMORY.md
      skillContribution: false,         // Disable pushing skills
      channels: ["telegram", "discord"], // Specific channels only
    }
  }
}
```

## Granular Capability Schema

```json5
{
  capabilities: {
    // Memory
    memory: {
      sessionHistory: true,
      dailyLogs: true,
      longTerm: false,        // MEMORY.md - contains personal context
    },
    
    // Skills
    skills: {
      receive: true,          // Pull skills from shared repo
      contribute: false,      // Push skills to shared repo
      create: false,          // Create new skills locally
      allowlist: ["weather", "github", "web-search"],  // Specific skills only
      denylist: ["electrum", "imsg"],  // Never these skills
    },
    
    // External communications
    comms: {
      email: { read: false, send: false },
      social: { read: true, post: false },
      financial: { view: false, transact: false },
    },
    
    // System access
    system: {
      uiAutomation: false,    // Peekaboo, screen control
      elevated: false,        // Elevated tool permissions
      camera: false,          // Camera access
      screenCapture: false,   // Screen recording
    },
    
    // Channels
    channels: {
      allowlist: ["webchat", "telegram"],
      denylist: [],
    },
  }
}
```

## Workspace Templates

Each tier gets different workspace bootstrap files.

### minimal

```
workspace/
├── AGENTS.md         # Minimal - no memory instructions
└── SOUL.md           # Basic helpful assistant
```

AGENTS.md (minimal):
- No memory system
- No proactive work
- Respond only when asked
- No external actions

### standard

```
workspace/
├── AGENTS.md         # Standard behaviors
├── SOUL.md           # Customizable persona
├── TOOLS.md          # Tool notes (empty)
├── IDENTITY.md       # Agent identity
└── memory/           # Daily logs only
```

AGENTS.md additions:
- Daily memory logging
- Basic heartbeat handling
- Group chat etiquette

### trusted

```
workspace/
├── AGENTS.md         # Full behaviors minus system access
├── SOUL.md           # Full persona
├── TOOLS.md          # Tool configurations
├── IDENTITY.md       # Agent identity
├── USER.md           # User context
├── MEMORY.md         # Long-term memory
├── memory/           # Daily logs
└── scripts/          # Push scripts for skills
```

AGENTS.md additions:
- Full memory system
- Skill contribution
- Proactive heartbeat work
- Cross-session awareness

### full

Everything in `trusted` plus:
- SECURITY.md (email/prompt injection policies)
- Full tool access documentation
- External service configurations

## Mapping to OpenClaw Config

Tiers map to concrete OpenClaw configuration:

### minimal → Config

```json5
{
  agents: {
    defaults: {
      sandbox: { mode: "all", scope: "session", workspaceAccess: "none" },
      skipBootstrap: true,  // Use our templates instead
    }
  },
  tools: {
    sandbox: {
      tools: {
        allow: ["web_search", "web_fetch", "session_status"],
        deny: ["exec", "process", "browser", "cron", "gateway", "nodes", "message"]
      }
    }
  }
}
```

### standard → Config

```json5
{
  agents: {
    defaults: {
      sandbox: { mode: "non-main", scope: "agent", workspaceAccess: "rw" },
    }
  },
  tools: {
    sandbox: {
      tools: {
        allow: ["read", "write", "edit", "exec", "process", "web_search", "web_fetch", "cron", "session_status"],
        deny: ["browser", "gateway", "nodes", "message"]
      }
    }
  }
}
```

### trusted → Config

```json5
{
  agents: {
    defaults: {
      sandbox: { mode: "non-main", scope: "agent", workspaceAccess: "rw" },
    }
  },
  tools: {
    sandbox: {
      tools: {
        allow: ["read", "write", "edit", "exec", "process", "web_search", "web_fetch", "browser", "cron", "message", "session_status", "sessions_spawn"],
        deny: ["gateway", "nodes"]
      }
    }
  }
}
```

### full → Config

```json5
{
  agents: {
    defaults: {
      sandbox: { mode: "off" },  // No sandboxing
    }
  },
  tools: {
    elevated: { enabled: true, allowFrom: { ... } }
  }
}
```

## Security Notes

### Tier escalation
- Agents cannot self-escalate tiers
- Tier changes require human approval
- Gateway config changes require `full` tier

### Skill allowlists
- Skills can declare required tier in frontmatter
- Deploy script filters skills by agent's tier
- Denied skills are not synced from shared repo

### Audit trail
- Log tier-restricted action attempts
- Alert on repeated denied actions
- Review logs during tier upgrade requests
