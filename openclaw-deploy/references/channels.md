# Channel Setup

## WhatsApp

**Type:** QR code pairing (Baileys Web)

### Setup Steps

1. Run channel login:
   ```bash
   openclaw channels login
   # or in Docker:
   docker compose run --rm openclaw-cli channels login
   ```

2. Scan QR code with WhatsApp mobile app
3. Configure allowlist

### Config

```json5
{
  channels: {
    whatsapp: {
      dmPolicy: "pairing",  // pairing | allowlist | open
      allowFrom: ["+15551234567"],
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

### Human Required
- [ ] Scan QR code with phone
- [ ] Phone must stay connected to internet

---

## Telegram

**Type:** Bot token

### Setup Steps

1. Create bot via @BotFather on Telegram
2. Get bot token
3. Add to config

### Config

```json5
{
  channels: {
    telegram: {
      enabled: true,
      botToken: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
      dmPolicy: "pairing",
      allowFrom: ["tg:123456789", "@username"],
      groups: {
        "*": { requireMention: true }
      }
    }
  }
}
```

Or via env: `TELEGRAM_BOT_TOKEN=123456789:ABC...`

### Human Required
- [ ] Create bot via @BotFather
- [ ] Copy bot token
- [ ] (Optional) Set bot commands, description, profile photo

---

## Discord

**Type:** Bot token (Gateway)

### Setup Steps

1. Create application: https://discord.com/developers/applications
2. Go to Bot section, create bot
3. Enable Message Content Intent
4. Generate invite link with permissions
5. Add bot to servers

### Required Intents
- Message Content (privileged)
- Guild Messages
- Direct Messages

### Required Permissions
- Read Messages/View Channels
- Send Messages
- Read Message History
- Add Reactions
- Use Slash Commands

### Config

```json5
{
  channels: {
    discord: {
      enabled: true,
      token: "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAuR2FiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6",
      dm: {
        enabled: true,
        policy: "pairing"
      },
      guilds: {
        "123456789012345678": {
          channels: {
            general: { allow: true, requireMention: true }
          }
        }
      }
    }
  }
}
```

Or via env: `DISCORD_BOT_TOKEN=MTIz...`

### Human Required
- [ ] Create Discord application
- [ ] Create bot and get token
- [ ] Enable Message Content Intent
- [ ] Generate invite link
- [ ] Add bot to servers

---

## Slack

**Type:** Socket Mode (bot + app tokens)

### Setup Steps

1. Create Slack app: https://api.slack.com/apps
2. Enable Socket Mode
3. Add bot scopes
4. Install to workspace
5. Get tokens

### Required Scopes (Bot)
- `app_mentions:read`
- `channels:history`
- `channels:read`
- `chat:write`
- `groups:history`
- `groups:read`
- `im:history`
- `im:read`
- `im:write`
- `reactions:read`
- `reactions:write`
- `users:read`

### Config

```json5
{
  channels: {
    slack: {
      enabled: true,
      botToken: "xoxb-...",
      appToken: "xapp-...",
      dm: {
        enabled: true,
        policy: "pairing"
      },
      channels: {
        "#general": { allow: true, requireMention: true }
      }
    }
  }
}
```

Or via env:
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

### Human Required
- [ ] Create Slack app
- [ ] Enable Socket Mode
- [ ] Add bot token scopes
- [ ] Install to workspace
- [ ] Copy bot token and app token

---

## Signal

**Type:** signal-cli (linked device)

### Setup Steps

1. Install signal-cli
2. Link as secondary device
3. Configure OpenClaw

### Installation

```bash
# macOS
brew install signal-cli

# Linux (manual)
# Download from https://github.com/AsamK/signal-cli/releases
```

### Linking

```bash
# Generate QR code
signal-cli link -n "OpenClaw"

# Scan with Signal mobile app
```

### Config

```json5
{
  channels: {
    signal: {
      enabled: true,
      number: "+15551234567",
      dmPolicy: "pairing",
      groupPolicy: "allowlist",
      groupAllowFrom: ["+15559876543"]
    }
  }
}
```

### Human Required
- [ ] Install signal-cli
- [ ] Link as secondary device (scan QR with phone)
- [ ] Phone must stay registered

---

## iMessage

**Type:** imsg CLI (macOS only)

### Requirements
- macOS with Messages app
- Full Disk Access for OpenClaw
- imsg CLI installed

### Setup

```bash
# Install imsg
brew tap pschmitt/tap
brew install imsg
```

### Config

```json5
{
  channels: {
    imessage: {
      enabled: true,
      cliPath: "imsg",
      dmPolicy: "pairing",
      allowFrom: ["+15551234567", "user@example.com"]
    }
  }
}
```

### Human Required
- [ ] Grant Full Disk Access to Terminal/OpenClaw
- [ ] Approve Messages automation prompt on first send

---

## Google Chat

**Type:** Webhook (Service Account)

### Setup Steps

1. Create Google Cloud project
2. Enable Chat API
3. Create service account
4. Create Chat app in Admin Console
5. Configure webhook

### Config

```json5
{
  channels: {
    googlechat: {
      enabled: true,
      serviceAccountFile: "/path/to/service-account.json",
      audienceType: "app-url",
      audience: "https://your-domain.com/googlechat",
      webhookPath: "/googlechat",
      dm: { enabled: true, policy: "pairing" }
    }
  }
}
```

### Human Required
- [ ] Create GCP project
- [ ] Enable Chat API
- [ ] Create service account
- [ ] Download service account JSON
- [ ] Create Chat app in Admin Console
- [ ] Configure app URL/webhook

---

## Webchat (Built-in)

**Type:** HTTP/WebSocket

Always available at gateway port. No additional setup needed.

### Config

```json5
{
  gateway: {
    port: 18789
  }
}
```

### Access
- Local: http://127.0.0.1:18789
- Remote: https://your-domain.com (with reverse proxy)

### Human Required
- [ ] (Optional) Set up reverse proxy for HTTPS
- [ ] (Optional) Configure DNS

---

## Multi-Account Setup

Each channel supports multiple accounts:

```json5
{
  channels: {
    telegram: {
      accounts: {
        default: { botToken: "token1" },
        alerts: { botToken: "token2" }
      }
    },
    whatsapp: {
      accounts: {
        default: {},
        business: {}
      }
    }
  }
}
```

Run separate onboarding for each account.
