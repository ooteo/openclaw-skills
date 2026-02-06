#!/usr/bin/env python3
"""
Generate human action checklist based on deployment configuration.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Generate human action checklist")
    parser.add_argument("--config", "-c", required=True, help="OpenClaw config file")
    parser.add_argument("--output", "-o", required=True, help="Output checklist file")
    parser.add_argument("--host", help="Remote host (user@ip)")
    parser.add_argument("--domain", help="Domain name")
    parser.add_argument("--port", type=int, default=18789, help="Gateway port")
    parser.add_argument("--ssl", action="store_true", help="SSL enabled")
    return parser.parse_args()


def load_config(config_file: str) -> dict:
    """Load OpenClaw config (JSON or JSON5)."""
    with open(config_file) as f:
        content = f.read()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Handle JSON5
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        content = re.sub(r",\s*([}\]])", r"\1", content)
        return json.loads(content)


def detect_required_api_keys(config: dict) -> list[tuple[str, str, str]]:
    """Detect which API keys are needed. Returns (provider, key_name, instructions)."""
    keys = []
    
    model_config = config.get("agents", {}).get("defaults", {}).get("model", {})
    primary = model_config.get("primary", "")
    fallbacks = model_config.get("fallbacks", [])
    
    all_models = [primary] + fallbacks
    
    providers_seen = set()
    
    for model in all_models:
        if not model:
            continue
        provider = model.split("/")[0].lower()
        
        if provider in providers_seen:
            continue
        providers_seen.add(provider)
        
        if provider == "anthropic":
            keys.append((
                "Anthropic",
                "ANTHROPIC_API_KEY",
                "https://console.anthropic.com/ → API Keys → Create"
            ))
        elif provider == "openai":
            keys.append((
                "OpenAI",
                "OPENAI_API_KEY",
                "https://platform.openai.com/api-keys → Create new secret key"
            ))
        elif provider == "openrouter":
            keys.append((
                "OpenRouter",
                "OPENROUTER_API_KEY",
                "https://openrouter.ai/keys → Create API key"
            ))
        elif provider == "venice":
            keys.append((
                "Venice AI",
                "VENICE_API_KEY",
                "https://venice.ai/ → API settings"
            ))
        elif provider == "ollama":
            keys.append((
                "Ollama (local)",
                "OLLAMA_API_KEY",
                "Set to 'ollama-local' (no real key needed)"
            ))
    
    return keys


def detect_channels(config: dict) -> list[str]:
    """Detect enabled channels."""
    channels = config.get("channels", {})
    enabled = []
    
    for channel in ["whatsapp", "telegram", "discord", "slack", "signal", "imessage", "googlechat"]:
        if channel in channels:
            ch_config = channels[channel]
            if ch_config.get("enabled", True):  # WhatsApp doesn't need enabled flag
                enabled.append(channel)
    
    return enabled


def generate_api_keys_section(keys: list[tuple[str, str, str]]) -> str:
    """Generate API keys section."""
    if not keys:
        return "_No API keys required._\n"
    
    lines = []
    for provider, key_name, instructions in keys:
        lines.append(f"### {provider}")
        lines.append(f"- [ ] Go to: {instructions}")
        lines.append(f"- [ ] Copy the API key")
        lines.append(f"- [ ] Add to `.env`: `{key_name}=<your-key>`")
        lines.append("")
    
    return "\n".join(lines)


def generate_channel_section(channel: str) -> str:
    """Generate setup instructions for a channel."""
    
    CHANNEL_INSTRUCTIONS = {
        "whatsapp": """### WhatsApp
- [ ] Run: `openclaw channels login` (or `docker compose run --rm openclaw-cli channels login`)
- [ ] Open WhatsApp on your phone
- [ ] Go to Settings → Linked Devices → Link a Device
- [ ] Scan the QR code displayed in terminal
- [ ] Wait for "Connected" confirmation

**Important:** Your phone must maintain internet connectivity for WhatsApp to work.
""",
        
        "telegram": """### Telegram Bot
- [ ] Open Telegram and search for @BotFather
- [ ] Send `/newbot` command
- [ ] Choose a display name for your bot
- [ ] Choose a username (must end in `bot`, e.g., `myassistant_bot`)
- [ ] Copy the bot token (looks like `123456789:ABCdef...`)
- [ ] Add to `.env`: `TELEGRAM_BOT_TOKEN=<your-token>`

**Optional customization with @BotFather:**
- [ ] `/setdescription` — Set bot description
- [ ] `/setabouttext` — Set about text
- [ ] `/setuserpic` — Upload profile photo
- [ ] `/setcommands` — Set command menu
""",
        
        "discord": """### Discord Bot
- [ ] Go to https://discord.com/developers/applications
- [ ] Click "New Application" and name it
- [ ] Go to "Bot" section in the sidebar
- [ ] Click "Add Bot" (or "Reset Token" if bot exists)
- [ ] **Enable "Message Content Intent"** under Privileged Gateway Intents
- [ ] Copy the bot token
- [ ] Add to `.env`: `DISCORD_BOT_TOKEN=<your-token>`

**Generate invite link:**
- [ ] Go to "OAuth2" → "URL Generator"
- [ ] Under "Scopes", select: `bot`, `applications.commands`
- [ ] Under "Bot Permissions", select:
  - Read Messages/View Channels
  - Send Messages
  - Read Message History
  - Add Reactions
  - Use Slash Commands
- [ ] Copy the generated URL
- [ ] Open URL in browser and add bot to your server(s)
""",
        
        "slack": """### Slack App
- [ ] Go to https://api.slack.com/apps
- [ ] Click "Create New App" → "From scratch"
- [ ] Name your app and select workspace
- [ ] Go to "Socket Mode" and enable it
- [ ] Generate an App-Level Token with `connections:write` scope
- [ ] Copy the app token (starts with `xapp-`)
- [ ] Go to "OAuth & Permissions"
- [ ] Add these Bot Token Scopes:
  - `app_mentions:read`
  - `channels:history`, `channels:read`
  - `chat:write`
  - `groups:history`, `groups:read`
  - `im:history`, `im:read`, `im:write`
  - `reactions:read`, `reactions:write`
  - `users:read`
- [ ] Click "Install to Workspace"
- [ ] Copy the Bot User OAuth Token (starts with `xoxb-`)
- [ ] Add to `.env`:
  ```
  SLACK_BOT_TOKEN=xoxb-...
  SLACK_APP_TOKEN=xapp-...
  ```
""",
        
        "signal": """### Signal (signal-cli)
- [ ] Install signal-cli:
  - macOS: `brew install signal-cli`
  - Linux: Download from https://github.com/AsamK/signal-cli/releases
- [ ] Run: `signal-cli link -n "OpenClaw"`
- [ ] A QR code will be displayed
- [ ] On your phone: Signal → Settings → Linked Devices → Link New Device
- [ ] Scan the QR code
- [ ] Note your phone number for config

**Note:** Your phone must remain registered with Signal for the link to work.
""",
        
        "imessage": """### iMessage (macOS only)
- [ ] Install imsg CLI:
  ```bash
  brew tap pschmitt/tap
  brew install imsg
  ```
- [ ] Grant Full Disk Access:
  - System Preferences → Privacy & Security → Full Disk Access
  - Add Terminal (or your terminal app)
  - If running as daemon, add the OpenClaw process
- [ ] Test installation: `imsg chats --limit 5`
- [ ] On first message send, approve the automation prompt

**Note:** iMessage channel only works on macOS with Messages app configured.
""",
        
        "googlechat": """### Google Chat
- [ ] Go to https://console.cloud.google.com/
- [ ] Create a new project (or select existing)
- [ ] Enable "Google Chat API" (APIs & Services → Enable APIs)
- [ ] Go to "IAM & Admin" → "Service Accounts"
- [ ] Create a service account
- [ ] Create and download a JSON key file
- [ ] Store the JSON file securely (e.g., `~/.openclaw/google-chat-sa.json`)
- [ ] Go to https://admin.google.com/ (requires Google Workspace admin)
- [ ] Navigate to Apps → Google Workspace → Chat
- [ ] Create a Chat app with:
  - App URL pointing to your OpenClaw webhook
  - Service account email for authentication
- [ ] Update config with service account file path
""",
    }
    
    return CHANNEL_INSTRUCTIONS.get(channel, f"### {channel.title()}\n_See OpenClaw docs for setup instructions._\n")


def generate_network_section(args) -> str:
    """Generate network/DNS section."""
    lines = []
    
    if args.domain:
        lines.append("### Domain & DNS")
        lines.append(f"- [ ] Ensure you own/control: `{args.domain}`")
        lines.append(f"- [ ] Create DNS A record pointing to your server IP:")
        lines.append(f"  - Host: `{args.domain.split('.')[0] if '.' in args.domain else '@'}`")
        lines.append(f"  - Points to: `<your-server-ip>`")
        lines.append(f"  - TTL: 300 (5 minutes)")
        lines.append(f"- [ ] Verify DNS propagation: `dig {args.domain}`")
        lines.append("")
    
    if args.ssl:
        lines.append("### SSL/TLS Certificate")
        lines.append("**Option A: Caddy (automatic)**")
        lines.append("- [ ] Install Caddy: https://caddyserver.com/docs/install")
        lines.append(f"- [ ] Add to Caddyfile:")
        lines.append(f"  ```")
        lines.append(f"  {args.domain} {{")
        lines.append(f"      reverse_proxy localhost:{args.port}")
        lines.append(f"  }}")
        lines.append(f"  ```")
        lines.append("- [ ] Start Caddy (auto-obtains Let's Encrypt certificate)")
        lines.append("")
        lines.append("**Option B: certbot + nginx**")
        lines.append("- [ ] Install certbot")
        lines.append(f"- [ ] Run: `sudo certbot certonly --standalone -d {args.domain}`")
        lines.append("- [ ] Configure nginx with generated certificates")
        lines.append("- [ ] Test renewal: `sudo certbot renew --dry-run`")
        lines.append("")
    
    if args.host:
        lines.append("### Firewall")
        lines.append("- [ ] Allow SSH (port 22)")
        lines.append("- [ ] Allow HTTP (port 80) for certificate renewal")
        lines.append("- [ ] Allow HTTPS (port 443)")
        if not args.ssl:
            lines.append(f"- [ ] Allow gateway port ({args.port})")
        lines.append("")
        lines.append("**UFW commands:**")
        lines.append("```bash")
        lines.append("sudo ufw allow 22/tcp")
        lines.append("sudo ufw allow 80/tcp")
        lines.append("sudo ufw allow 443/tcp")
        if not args.ssl:
            lines.append(f"sudo ufw allow {args.port}/tcp")
        lines.append("sudo ufw enable")
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines) if lines else "_No network configuration required._\n"


def generate_server_section(args) -> str:
    """Generate server access section."""
    if not args.host:
        return "_Local deployment — no remote server access needed._\n"
    
    user, host = args.host.split("@") if "@" in args.host else ("root", args.host)
    
    return f"""### SSH Access
- [ ] Verify SSH access: `ssh {args.host}`
- [ ] (Recommended) Set up SSH key authentication
- [ ] (Recommended) Disable password authentication

### Docker (if using Docker deployment)
- [ ] Verify Docker is installed: `docker --version`
- [ ] Verify Docker Compose: `docker compose version`
- [ ] If not installed:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker {user}
  # Log out and back in
  ```
"""


def generate_verification_section(args, channels: list[str]) -> str:
    """Generate verification section."""
    lines = ["### Gateway Status"]
    lines.append("- [ ] Check status: `openclaw status`")
    
    if args.host:
        if args.domain and args.ssl:
            lines.append(f"- [ ] Access Control UI: https://{args.domain}")
        else:
            lines.append(f"- [ ] Access Control UI: http://<server-ip>:{args.port}")
    else:
        lines.append(f"- [ ] Access Control UI: http://127.0.0.1:{args.port}")
    
    lines.append("- [ ] Check logs: `openclaw logs --tail 50`")
    lines.append("")
    
    if channels:
        lines.append("### Channel Verification")
        for channel in channels:
            lines.append(f"- [ ] Send test message via {channel.title()}")
            lines.append(f"- [ ] Verify response received via {channel.title()}")
        lines.append("")
    
    lines.append("### AI Verification")
    lines.append("- [ ] Send a simple prompt (e.g., 'Hello, what's 2+2?')")
    lines.append("- [ ] Verify response uses correct model")
    lines.append("- [ ] (If fallback configured) Test fallback by temporarily invalidating primary key")
    lines.append("")
    
    lines.append("### Persistence Check")
    lines.append("- [ ] Restart gateway: `openclaw gateway restart`")
    lines.append("- [ ] Verify sessions persist")
    lines.append("- [ ] Verify channel connections restore automatically")
    
    return "\n".join(lines)


def main():
    args = parse_args()
    
    config = load_config(args.config)
    api_keys = detect_required_api_keys(config)
    channels = detect_channels(config)
    
    # Build checklist
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    target = "remote" if args.host else "local"
    
    checklist = f"""# OpenClaw Deployment Checklist

**Generated:** {timestamp}
**Target:** {target}
{"**Host:** " + args.host if args.host else ""}
{"**Domain:** " + args.domain if args.domain else ""}
**Port:** {args.port}

---

## 🔑 API Keys & Credentials

{generate_api_keys_section(api_keys)}

---

## 📱 Channel Setup

{"".join(generate_channel_section(ch) for ch in channels) if channels else "_No messaging channels enabled._"}

---

## 🌐 Network & DNS

{generate_network_section(args)}

---

## 🖥️ Server Access

{generate_server_section(args)}

---

## ✅ Post-Deployment Verification

{generate_verification_section(args, channels)}

---

## 📝 Notes

_Add any deployment-specific notes here._

"""
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(checklist)
    
    print(f"✓ Checklist written to: {output_path}")
    
    # Summary
    print(f"\nChecklist Summary:")
    print(f"  API keys needed: {len(api_keys)}")
    print(f"  Channels to configure: {len(channels)}")
    if channels:
        print(f"    - {', '.join(channels)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
