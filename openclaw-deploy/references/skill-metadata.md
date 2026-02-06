# Skill Safety Metadata

Every skill should declare its requirements and risks in human-readable frontmatter.

## Frontmatter Schema

```yaml
---
name: skill-name
description: What this skill does and when to use it

# Platform requirements
platforms:
  - os: darwin | linux | windows | any
    arch: [arm64, x86_64]     # Optional, omit for "any"
    container: true | false   # Works in Docker/containers?

# System permissions required
permissions:
  - full-disk-access          # macOS: access to all files
  - messages-automation       # macOS: Messages.app control
  - accessibility             # macOS: UI scripting
  - camera                    # Camera access
  - microphone                # Microphone access
  - location                  # Location services
  - contacts                  # Address book access
  - calendar                  # Calendar access
  - network                   # Network/firewall changes
  - root                      # Requires sudo/admin

# Risk categories (for human review)
risks:
  - personal-data             # Accesses personal information
  - impersonation             # Can act as user (send messages, etc.)
  - financial                 # Handles money/transactions
  - system-changes            # Modifies system settings
  - network-exposure          # Opens ports, external connections
  - data-exfiltration         # Could leak data if misused

# Minimum capability tier
tier: minimal | standard | trusted | full

# External dependencies
dependencies:
  - name: tool-name
    install:
      brew: "brew install tool"
      apt: "apt-get install tool"
      manual: "Download from https://..."
    check: "command -v tool"
    version: ">=1.0.0"         # Optional version constraint
---
```

## Examples

### Low-risk skill (weather)

```yaml
---
name: weather
description: Get current weather and forecasts (no API key required)
platforms:
  - os: any
    container: true
permissions: []
risks: []
tier: minimal
dependencies:
  - name: curl
    check: "command -v curl"
---
```

### Medium-risk skill (github)

```yaml
---
name: github
description: Interact with GitHub using the gh CLI
platforms:
  - os: any
    container: true
permissions: []
risks:
  - network-exposure          # API calls to GitHub
tier: standard
dependencies:
  - name: gh
    install:
      brew: "brew install gh"
      apt: "apt-get install gh"
    check: "command -v gh"
---
```

### High-risk skill (imsg)

```yaml
---
name: imsg
description: iMessage/SMS CLI for listing chats, history, and sending
platforms:
  - os: darwin
    container: false
permissions:
  - full-disk-access          # Read Messages database
  - messages-automation       # Send via Messages.app
risks:
  - personal-data             # Reads message history
  - impersonation             # Can send messages as user
tier: full
dependencies:
  - name: imsg
    install:
      brew: "brew tap pschmitt/tap && brew install imsg"
    check: "command -v imsg"
---
```

### Financial skill (electrum)

```yaml
---
name: electrum
description: Manage Bitcoin wallet via Electrum CLI
platforms:
  - os: [darwin, linux]
    container: false          # Needs GUI or daemon mode
permissions: []
risks:
  - financial                 # Handles real money
  - personal-data             # Wallet addresses, balances
tier: full
dependencies:
  - name: electrum
    install:
      brew: "brew install --cask electrum"
      manual: "Download from https://electrum.org"
    check: "command -v electrum || [ -d /Applications/Electrum.app ]"
---
```

## Risk Definitions

### personal-data
Skill can access, read, or process personal information:
- Messages, emails, contacts
- Browsing history
- Documents, photos
- Location data

**Human should know:** This skill can see your private stuff.

### impersonation
Skill can act as the user externally:
- Send emails
- Post to social media
- Send messages
- Make API calls on user's behalf

**Human should know:** This skill can pretend to be you.

### financial
Skill handles money or financial data:
- Cryptocurrency transactions
- Bank account access
- Payment processing
- Financial account credentials

**Human should know:** This skill can spend your money.

### system-changes
Skill modifies system configuration:
- Install software
- Change settings
- Modify startup items
- Edit system files

**Human should know:** This skill can change how your computer works.

### network-exposure
Skill opens network connections or ports:
- Runs servers
- Opens firewall ports
- Makes external API calls
- Downloads/uploads data

**Human should know:** This skill talks to the internet.

### data-exfiltration
Skill could potentially leak data if compromised:
- Combines read access with network access
- Could forward data externally
- Has broad file system access

**Human should know:** A bug or attack could leak your data.

## Permission Definitions (macOS)

| Permission | System Preferences Location | Why Needed |
|------------|---------------------------|------------|
| full-disk-access | Privacy & Security → Full Disk Access | Read protected files (Messages.db, etc.) |
| accessibility | Privacy & Security → Accessibility | UI scripting, click simulation |
| messages-automation | (prompted on first use) | Control Messages.app |
| camera | Privacy & Security → Camera | Take photos/video |
| microphone | Privacy & Security → Microphone | Record audio |
| location | Privacy & Security → Location Services | Get GPS coordinates |
| contacts | Privacy & Security → Contacts | Read address book |
| calendar | Privacy & Security → Calendar | Read/write events |

## Using Metadata in Deployment

The deploy script filters skills by:

1. **Platform compatibility** - Skip skills that can't run
2. **Tier requirement** - Skip skills above agent's tier
3. **Risk allowlist** - Only include risks the human approved

```python
def filter_skills_for_agent(all_skills: list, agent_spec: dict, platform: dict) -> list:
    """Filter skills based on agent capabilities and platform."""
    
    agent_tier = agent_spec.get("capabilities", {}).get("tier", "minimal")
    tier_order = ["minimal", "standard", "trusted", "full"]
    agent_tier_idx = tier_order.index(agent_tier)
    
    allowed_risks = agent_spec.get("capabilities", {}).get("allowedRisks", [])
    
    filtered = []
    for skill in all_skills:
        meta = skill.get("metadata", {})
        
        # Check platform
        if not is_platform_compatible(meta.get("platforms", []), platform):
            continue
        
        # Check tier
        skill_tier = meta.get("tier", "minimal")
        if tier_order.index(skill_tier) > agent_tier_idx:
            continue
        
        # Check risks
        skill_risks = meta.get("risks", [])
        if skill_risks and not all(r in allowed_risks for r in skill_risks):
            continue
        
        filtered.append(skill)
    
    return filtered
```

## Human-Readable Summary

When deploying, show the human:

```
📋 Skill Safety Summary

WILL INSTALL (5 skills):
  ✓ weather          [minimal] No special permissions
  ✓ github           [standard] Network access only
  ✓ web-search       [minimal] No special permissions
  ✓ video-frames     [standard] No special permissions
  ✓ skill-creator    [trusted] No special permissions

SKIPPED - Platform incompatible (2 skills):
  ✗ imsg             Requires macOS (you're on Linux)
  ✗ apple-notes      Requires macOS (you're on Linux)

SKIPPED - Above agent tier (3 skills):
  ✗ electrum         Requires 'full' tier (agent is 'standard')
  ✗ peekaboo         Requires 'full' tier (agent is 'standard')
  ✗ bird             Requires 'trusted' tier (agent is 'standard')

SKIPPED - Unapproved risks (1 skill):
  ✗ email-client     Risk 'impersonation' not approved

Proceed? [y/N]
```
