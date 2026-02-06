# Human-Required Steps

This file contains templates for generating human checklists based on deployment configuration.

## Master Checklist Template

```markdown
# OpenClaw Deployment Checklist

Generated: {timestamp}
Target: {target}
Host: {host}

## 🔑 API Keys & Credentials

{api_keys_section}

## 📱 Channel Setup

{channels_section}

## 🌐 Network & DNS

{network_section}

## 🖥️ Server Access

{server_section}

## ✅ Post-Deployment Verification

{verification_section}
```

---

## API Keys Section Templates

### Anthropic
```markdown
### Anthropic API Key
- [ ] Go to: https://console.anthropic.com/
- [ ] Create account or sign in
- [ ] Navigate to API Keys
- [ ] Create new API key
- [ ] Copy key (starts with `sk-ant-`)
- [ ] Add to deployment: `ANTHROPIC_API_KEY=sk-ant-...`
```

### OpenAI
```markdown
### OpenAI API Key
- [ ] Go to: https://platform.openai.com/api-keys
- [ ] Create account or sign in
- [ ] Create new secret key
- [ ] Copy key (starts with `sk-`)
- [ ] Add to deployment: `OPENAI_API_KEY=sk-...`
```

### OpenRouter
```markdown
### OpenRouter API Key
- [ ] Go to: https://openrouter.ai/keys
- [ ] Create account or sign in
- [ ] Create new API key
- [ ] Copy key (starts with `sk-or-`)
- [ ] Add to deployment: `OPENROUTER_API_KEY=sk-or-...`
```

### Venice AI
```markdown
### Venice AI API Key
- [ ] Go to: https://venice.ai/
- [ ] Create account
- [ ] Navigate to API settings
- [ ] Generate API key
- [ ] Add to deployment: `VENICE_API_KEY=...`
```

---

## Channel Section Templates

### WhatsApp
```markdown
### WhatsApp
- [ ] Have phone with WhatsApp ready
- [ ] Run: `openclaw channels login`
- [ ] Scan QR code with WhatsApp app (Linked Devices)
- [ ] Wait for "Connected" confirmation
- [ ] Keep phone connected to internet

**Note:** WhatsApp requires the linked phone to maintain internet connectivity.
```

### Telegram
```markdown
### Telegram Bot
- [ ] Open Telegram, find @BotFather
- [ ] Send `/newbot`
- [ ] Choose bot name (display name)
- [ ] Choose username (must end in `bot`)
- [ ] Copy the bot token
- [ ] Add to config: `channels.telegram.botToken`

**Optional customization:**
- [ ] `/setdescription` - Bot description
- [ ] `/setabouttext` - About text
- [ ] `/setuserpic` - Profile photo
- [ ] `/setcommands` - Command menu
```

### Discord
```markdown
### Discord Bot
- [ ] Go to: https://discord.com/developers/applications
- [ ] Click "New Application"
- [ ] Name your application
- [ ] Go to "Bot" section
- [ ] Click "Add Bot"
- [ ] Enable "Message Content Intent" (under Privileged Gateway Intents)
- [ ] Copy the bot token
- [ ] Add to config: `channels.discord.token`

**Generate invite link:**
- [ ] Go to "OAuth2" > "URL Generator"
- [ ] Select scopes: `bot`, `applications.commands`
- [ ] Select permissions:
  - Read Messages/View Channels
  - Send Messages
  - Read Message History
  - Add Reactions
  - Use Slash Commands
- [ ] Copy generated URL
- [ ] Open URL and add bot to your server(s)
```

### Slack
```markdown
### Slack App
- [ ] Go to: https://api.slack.com/apps
- [ ] Click "Create New App" > "From scratch"
- [ ] Name app, select workspace
- [ ] Go to "Socket Mode", enable it
- [ ] Generate App-Level Token with `connections:write` scope
- [ ] Copy app token (starts with `xapp-`)
- [ ] Go to "OAuth & Permissions"
- [ ] Add Bot Token Scopes:
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
- [ ] Install to Workspace
- [ ] Copy Bot User OAuth Token (starts with `xoxb-`)
- [ ] Add to config: `channels.slack.botToken` and `channels.slack.appToken`
```

### Signal
```markdown
### Signal (signal-cli)
- [ ] Install signal-cli:
  ```bash
  # macOS
  brew install signal-cli
  
  # Linux: download from GitHub releases
  ```
- [ ] Run: `signal-cli link -n "OpenClaw"`
- [ ] Scan QR code with Signal app (Linked Devices)
- [ ] Note your phone number for config
- [ ] Add to config: `channels.signal.number`

**Note:** Signal registration is tied to a phone number. The phone must remain registered.
```

### iMessage
```markdown
### iMessage (macOS only)
- [ ] Install imsg CLI:
  ```bash
  brew tap pschmitt/tap
  brew install imsg
  ```
- [ ] Grant Full Disk Access:
  - System Preferences > Privacy & Security > Full Disk Access
  - Add Terminal (or your terminal app)
  - Add OpenClaw if running as daemon
- [ ] Test: `imsg chats --limit 5`
- [ ] On first message send, approve automation prompt
```

### Google Chat
```markdown
### Google Chat
- [ ] Go to: https://console.cloud.google.com/
- [ ] Create new project (or select existing)
- [ ] Enable "Google Chat API"
- [ ] Go to "IAM & Admin" > "Service Accounts"
- [ ] Create service account
- [ ] Download JSON key file
- [ ] Go to: https://admin.google.com/ (requires admin)
- [ ] Apps > Google Workspace > Chat
- [ ] Create Chat app
- [ ] Configure webhook URL to your OpenClaw instance
- [ ] Copy service account JSON path to config
```

---

## Network Section Templates

### Domain & DNS
```markdown
### Domain Configuration
- [ ] Register/own domain: {domain}
- [ ] Create DNS A record:
  - Host: `{subdomain}` (or `@` for apex)
  - Points to: `{server_ip}`
  - TTL: 300 (5 minutes for testing)
- [ ] Wait for DNS propagation (check with `dig {domain}`)
```

### SSL/TLS
```markdown
### SSL Certificate
**Using Caddy (automatic):**
- [ ] Install Caddy
- [ ] Add to Caddyfile:
  ```
  {domain} {
      reverse_proxy localhost:18789
  }
  ```
- [ ] Start Caddy (auto-obtains certificate)

**Using certbot (Let's Encrypt):**
- [ ] Install certbot
- [ ] Run: `sudo certbot certonly --standalone -d {domain}`
- [ ] Configure nginx/reverse proxy with certs
- [ ] Set up auto-renewal: `sudo certbot renew --dry-run`
```

### Firewall
```markdown
### Firewall Configuration
- [ ] Allow SSH: port 22
- [ ] Allow HTTP: port 80 (for cert renewal)
- [ ] Allow HTTPS: port 443
- [ ] (If no proxy) Allow gateway: port {port}

**UFW commands:**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```
```

---

## Server Section Templates

### SSH Access
```markdown
### SSH Access
- [ ] Obtain server IP: {server_ip}
- [ ] Obtain SSH credentials (user/key)
- [ ] Test connection: `ssh {user}@{server_ip}`
- [ ] (Recommended) Set up SSH key authentication
- [ ] (Recommended) Disable password authentication
```

### Docker Installation
```markdown
### Docker Installation
- [ ] SSH into server
- [ ] Install Docker:
  ```bash
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  ```
- [ ] Log out and back in
- [ ] Verify: `docker --version`
- [ ] Verify: `docker compose version`
```

### GPU Setup (for local AI)
```markdown
### GPU Setup (NVIDIA)
- [ ] Verify NVIDIA driver: `nvidia-smi`
- [ ] Install NVIDIA Container Toolkit:
  ```bash
  distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
  curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
  curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  sudo systemctl restart docker
  ```
- [ ] Verify GPU in Docker: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`
```

---

## Verification Section Template

```markdown
### Post-Deployment Verification

**Gateway:**
- [ ] Check gateway status: `openclaw status`
- [ ] Access Control UI: http://{host}:{port}
- [ ] Check logs: `openclaw logs --tail 50`

**Channels:**
- [ ] Send test message via each enabled channel
- [ ] Verify responses are received
- [ ] Check channel connection status in logs

**AI:**
- [ ] Send a simple prompt
- [ ] Verify response uses configured model
- [ ] Test fallback (if configured) by simulating failure

**Persistence:**
- [ ] Restart gateway: `openclaw gateway restart`
- [ ] Verify sessions persist
- [ ] Verify channel connections restore
```

---

## Combined Example

For a deployment with Anthropic + Ollama + WhatsApp + Telegram on a VPS:

```markdown
# OpenClaw Deployment Checklist

Generated: 2026-02-06
Target: docker-remote
Host: deploy@myserver.com

## 🔑 API Keys & Credentials

### Anthropic API Key
- [ ] Go to: https://console.anthropic.com/
- [ ] Create API key
- [ ] Add to .env: `ANTHROPIC_API_KEY=sk-ant-...`

## 📱 Channel Setup

### WhatsApp
- [ ] Run: `openclaw channels login`
- [ ] Scan QR code with phone

### Telegram Bot
- [ ] Create bot via @BotFather
- [ ] Copy token to config

## 🌐 Network & DNS

### Domain Configuration
- [ ] Create A record: openclaw.myserver.com → server IP
- [ ] Wait for propagation

### SSL Certificate
- [ ] Install Caddy
- [ ] Configure reverse proxy

## 🖥️ Server Access

### SSH Access
- [ ] Test: `ssh deploy@myserver.com`

### Docker Installation
- [ ] Install Docker on server
- [ ] Verify with `docker --version`

## ✅ Post-Deployment Verification

- [ ] Check gateway: `openclaw status`
- [ ] Send test WhatsApp message
- [ ] Send test Telegram message
- [ ] Verify both respond correctly
```
