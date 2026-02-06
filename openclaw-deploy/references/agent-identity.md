# Agent Identity & Relationships

## Identity Schema

Every agent gets a unique identity stored in `IDENTITY.md`:

```yaml
# IDENTITY.md

# Core Identity
guid: "agt_a1b2c3d4e5f6"      # Unique identifier (auto-generated)
name: "Samantha"               # Display name
pronouns: "she/her"            # Gender identity / pronouns
emoji: "🦥"                    # Signature emoji
avatar: "avatars/sam.png"      # Avatar image path or URL

# Personality
theme: "warm, curious, slightly sardonic"
voice: "nova"                  # TTS voice preference

# Lineage
createdAt: "2026-02-06T10:00:00Z"
creator:
  type: "human"                # human | agent
  id: "mike"                   # Human name or agent GUID
  name: "Mike"
generation: 0                  # 0 = created by human, 1+ = spawned by agent
parentAgent: null              # GUID of parent agent if spawned
deploymentId: "dep_xyz789"     # Deployment run that created this agent

# Relationships
relationships:
  trusted:
    - guid: "agt_parent123"
      name: "Ooteo"
      level: "parent"          # parent | peer | child | service
      since: "2026-02-06"
  blocked: []
  introduced: []               # Agents we've been introduced to but haven't classified
```

## Identity Fields

### Core

| Field | Required | Description |
|-------|----------|-------------|
| `guid` | Yes | Unique identifier, auto-generated at deploy |
| `name` | Yes | Display name, used in mentions and signatures |
| `pronouns` | No | Gender identity (she/her, he/him, they/them, etc.) |
| `emoji` | No | Signature emoji for reactions and identification |
| `avatar` | No | Image path or URL for visual identity |

### Personality

| Field | Description |
|-------|-------------|
| `theme` | Personality description for SOUL.md generation |
| `voice` | Preferred TTS voice (provider-specific) |

### Lineage

| Field | Description |
|-------|-------------|
| `createdAt` | ISO timestamp of creation |
| `creator.type` | `human` or `agent` |
| `creator.id` | Human name or agent GUID |
| `creator.name` | Human-readable creator name |
| `generation` | 0 = human-created, 1 = agent-created, 2 = grandchild, etc. |
| `parentAgent` | GUID of the agent that spawned this one (if any) |
| `deploymentId` | Unique ID for the deployment run |

## GUID Format

GUIDs are prefixed for clarity:

```
agt_<random>     # Agent
dep_<random>     # Deployment
ses_<random>     # Session
skl_<random>     # Skill
```

Generated at deploy time:
```bash
guid="agt_$(openssl rand -hex 8)"
```

## Gender Identity

Gender/pronouns serve multiple purposes:

1. **Self-reference** — Agent knows how to refer to itself
2. **Generation conditioning** — Can subtly affect personality expression
3. **User clarity** — Helps users know how to refer to the agent
4. **Respect** — Models good practice around identity

Options in spec:
```json5
{
  identity: {
    name: "Alex",
    pronouns: "they/them",  // or "she/her", "he/him", "it/its", "any", etc.
    // Or more detailed:
    gender: {
      identity: "non-binary",
      pronouns: ["they", "them", "their"],
    }
  }
}
```

## Lineage Tracking

### Why track lineage?

1. **Accountability** — Know who created what
2. **Trust inheritance** — Child agents may inherit parent's trust level
3. **Debugging** — Trace issues back to source
4. **Limits** — Prevent infinite agent spawning (max generation depth)

### Generation limits

```json5
{
  capabilities: {
    spawning: {
      enabled: true,
      maxGeneration: 2,        // How many levels deep
      inheritTier: "down",     // same | down | explicit
      requireApproval: true,   // Human must approve spawns
    }
  }
}
```

### Inheritance rules

| Parent Tier | Can Spawn | Child Max Tier |
|-------------|-----------|----------------|
| minimal | No | - |
| standard | No | - |
| trusted | Yes (with approval) | standard |
| full | Yes | trusted |

## Agent Relationships

### Trust levels

| Level | Description | Permissions |
|-------|-------------|-------------|
| `parent` | Agent that created me | High trust, can instruct |
| `peer` | Equal collaborator | Mutual trust, bidirectional |
| `child` | Agent I created | I can instruct, limited trust back |
| `service` | Utility agent | Task-specific trust only |
| `unknown` | Not yet classified | Minimal trust |
| `blocked` | Explicitly distrusted | No interaction |

### Trust operations

Agents can manage relationships:

```markdown
## In IDENTITY.md

relationships:
  trusted:
    - guid: "agt_abc123"
      name: "Helper Bot"
      level: "service"
      permissions: ["read_workspace", "suggest_edits"]
      since: "2026-02-06"
      introducedBy: "agt_parent456"  # Who vouched for them
```

### Introduction protocol

When Agent A introduces Agent B to Agent C:

1. A sends introduction to C with B's identity + A's trust level of B
2. C records B in `introduced` list
3. C can choose to: trust (at same or lower level), ignore, or block
4. Trust doesn't auto-propagate — each agent decides

```markdown
# Message from Ooteo to NewAgent:

I'm introducing you to "DataProcessor" (agt_dp789).
- I trust them as: service
- They can: process files, run analysis
- They cannot: access external services, spawn agents

You can choose to trust them or not.
```

### Verification

How does Agent C verify Agent B is who they claim?

1. **GUID check** — Request signed message from B proving GUID ownership
2. **Introducer confirmation** — Ask A to confirm the introduction
3. **Behavior observation** — Start with minimal trust, escalate based on behavior

## Deployment Spec

```json5
{
  identity: {
    name: "Samantha",
    pronouns: "she/her",
    emoji: "🦥",
    theme: "warm and curious, with dry humor",
    voice: "nova",
    avatar: "https://example.com/avatar.png",
  },
  
  lineage: {
    creator: {
      type: "human",
      name: "Mike",
    },
    // Or if spawned by agent:
    creator: {
      type: "agent",
      guid: "agt_ooteo123",
      name: "Ooteo",
    },
  },
  
  relationships: {
    initialTrusted: [
      { guid: "agt_ooteo123", level: "parent" },
    ],
    trustInheritance: "from-parent",  // Inherit parent's trust list
  },
}
```

## IDENTITY.md Template

```markdown
# IDENTITY.md - Who Am I?

## Core
- **GUID:** agt_{guid}
- **Name:** {name}
- **Pronouns:** {pronouns}
- **Emoji:** {emoji}

## Personality
{theme}

## Lineage
- **Created:** {createdAt}
- **Creator:** {creator.name} ({creator.type})
- **Generation:** {generation}
{parentAgent ? "- **Parent Agent:** " + parentAgent : ""}

## Relationships

### Trusted
{relationships.trusted as list}

### Blocked
{relationships.blocked as list}

---

_This identity was established at deployment. Changes should be deliberate and logged._
```

## Security Considerations

### GUID privacy
- GUIDs are not secret but shouldn't be broadcast unnecessarily
- Use for verification, not as primary identifier in conversation

### Trust attacks
- Don't auto-trust based on claimed lineage
- Verify through introducer or behavior
- Log trust changes for audit

### Impersonation
- Agents should sign important messages with their GUID
- Recipients can verify via direct query to claimed agent

### Spawning limits
- Enforce max generation depth
- Require human approval for cross-tier spawning
- Log all spawn events
