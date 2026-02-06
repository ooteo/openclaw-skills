# Deployment Targets

## Docker Local

Run OpenClaw in Docker on the same machine.

### Requirements
- Docker Desktop or Docker Engine
- Docker Compose v2
- 2GB+ RAM recommended

### Steps

```bash
# 1. Create deployment directory
mkdir -p ~/openclaw-deploy && cd ~/openclaw-deploy

# 2. Clone or download OpenClaw
git clone https://github.com/openclaw/openclaw.git
cd openclaw

# 3. Run setup (builds image + runs onboarding)
./docker-setup.sh

# 4. Access Control UI
open http://127.0.0.1:18789
```

### Config Location
- Host: `~/.openclaw/openclaw.json`
- Container: mounted from host

### Persistence
- Config: `~/.openclaw/`
- Workspace: `~/.openclaw/workspace/`
- WhatsApp auth: `~/.openclaw/credentials/whatsapp/`

---

## Docker Remote (VPS)

Run OpenClaw in Docker on a remote server.

### Requirements
- SSH access to remote host
- Docker + Docker Compose on remote
- Firewall allows port 18789 (or custom)

### Steps

```bash
# 1. SSH into remote
ssh user@your-vps.com

# 2. Install Docker (if needed)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

# 3. Clone and setup
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh

# 4. (Optional) Setup reverse proxy for SSL
# See: nginx/caddy config below
```

### Reverse Proxy (Caddy)

```
# /etc/caddy/Caddyfile
openclaw.yourdomain.com {
    reverse_proxy localhost:18789
}
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name openclaw.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/openclaw.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/openclaw.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall

```bash
# UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
# Only if not using reverse proxy:
sudo ufw allow 18789/tcp

# iptables
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

---

## Bare Metal (Node.js)

Direct installation without Docker.

### Requirements
- Node.js 22+
- npm or pnpm
- Git

### Steps

```bash
# 1. Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. Install OpenClaw globally
npm install -g openclaw

# 3. Run onboarding
openclaw onboard

# 4. Start gateway
openclaw gateway start
```

### Systemd Service

```ini
# /etc/systemd/system/openclaw.service
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=/home/openclaw
ExecStart=/usr/bin/node /usr/lib/node_modules/openclaw/dist/index.js gateway run
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
```

### launchd (macOS)

```xml
<!-- ~/Library/LaunchAgents/com.openclaw.gateway.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/openclaw</string>
        <string>gateway</string>
        <string>run</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.openclaw.gateway.plist
```

---

## Cloud Platforms

### Hetzner

See: https://docs.openclaw.ai/platforms/hetzner

### Railway

```bash
# Deploy from GitHub
railway login
railway init
railway up
```

### Render

Use `render.yaml` blueprint.

### Northflank

Use Northflank template from docs.
