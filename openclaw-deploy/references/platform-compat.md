# Platform Compatibility

Deployment must account for what's actually possible on the target platform.

## Platform Detection

The deploy script detects:

```bash
OS=$(uname -s)           # Darwin, Linux, Windows (via WSL)
ARCH=$(uname -m)         # x86_64, arm64, aarch64
CONTAINER=$(cat /proc/1/cgroup 2>/dev/null | grep -q docker && echo "docker")
```

## Platform Matrix

| Feature | macOS (arm64) | macOS (x86) | Linux (x86) | Linux (arm) | Docker | WSL |
|---------|---------------|-------------|-------------|-------------|--------|-----|
| **Channels** |
| WhatsApp | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Telegram | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Discord | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Slack | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Signal | ✓ | ✓ | ✓ | ✓ | ⚠️ | ✓ |
| iMessage | ✓ | ✓ | - | - | - | - |
| Google Chat | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Local AI** |
| Ollama | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| GPU (NVIDIA) | - | - | ✓ | ✓ | ✓ | ✓ |
| GPU (Apple Silicon) | ✓ | - | - | - | - | - |
| GPU (AMD ROCm) | - | - | ⚠️ | - | ⚠️ | - |
| **Skills** |
| imsg (iMessage CLI) | ✓ | ✓ | - | - | - | - |
| peekaboo (UI auto) | ✓ | ✓ | - | - | - | - |
| apple-notes | ✓ | ✓ | - | - | - | - |
| apple-reminders | ✓ | ✓ | - | - | - | - |
| raycast | ✓ | ✓ | - | - | - | - |
| keeping-you-awake | ✓ | ✓ | - | - | - | - |
| electrum (Bitcoin) | ✓ | ✓ | ✓ | ✓ | ⚠️ | ✓ |
| bird (X/Twitter) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| github | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| weather | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **System** |
| Browser automation | ✓ | ✓ | ✓ | ⚠️ | ⚠️ | ✓ |
| Screen capture | ✓ | ✓ | ✓ | ✓ | - | - |
| Camera | ✓ | ✓ | ✓ | ✓ | - | - |

Legend: ✓ = Full support, ⚠️ = Limited/complex setup, - = Not available

## Skill Metadata Schema

Skills should declare platform requirements in SKILL.md frontmatter:

```yaml
---
name: imsg
description: iMessage/SMS CLI for macOS
platforms:
  - os: darwin              # darwin, linux, windows
    arch: [arm64, x86_64]   # Optional, defaults to all
    container: false        # Works in containers?
permissions:
  - full-disk-access        # macOS permission
  - messages-automation     # macOS automation
risks:
  - personal-data           # Accesses personal messages
  - impersonation           # Can send as user
tier: full                  # Minimum capability tier required
dependencies:
  - name: imsg
    install: "brew tap pschmitt/tap && brew install imsg"
    check: "command -v imsg"
---
```

## Platform-Specific Installation

### Package Managers

| Platform | Package Manager | Install Command |
|----------|-----------------|-----------------|
| macOS | Homebrew | `brew install <pkg>` |
| Debian/Ubuntu | apt | `apt-get install <pkg>` |
| RHEL/Fedora | dnf | `dnf install <pkg>` |
| Alpine | apk | `apk add <pkg>` |
| Arch | pacman | `pacman -S <pkg>` |

### Detection Script

```bash
detect_package_manager() {
    if command -v brew &>/dev/null; then
        echo "brew"
    elif command -v apt-get &>/dev/null; then
        echo "apt"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v apk &>/dev/null; then
        echo "apk"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    else
        echo "unknown"
    fi
}
```

## Incompatible Combinations

The deploy script should **error** on these:

| Requested | Platform | Reason |
|-----------|----------|--------|
| iMessage channel | Linux/Docker | macOS only |
| Apple Notes skill | Linux/Docker | macOS only |
| peekaboo skill | Linux/Docker | macOS only |
| NVIDIA GPU + Ollama | macOS | No NVIDIA support |
| Screen capture | Docker | No display |
| Camera | Docker | No hardware access |
| Signal | Docker (rootless) | Needs dbus, complex |

## Graceful Degradation

When a feature isn't available, the deploy script should:

1. **Warn** but continue if optional
2. **Error** if required
3. **Suggest alternatives** when possible

Example:
```
⚠️ iMessage not available on Linux
   Alternatives: WhatsApp, Signal, Telegram
   
   Continuing without iMessage channel...
```

## Docker-Specific Considerations

### What works in Docker
- All cloud-based channels (WhatsApp/Telegram/Discord/Slack)
- Ollama (with GPU passthrough for NVIDIA)
- Most file/exec operations
- Web search/fetch

### What doesn't work in Docker
- macOS-specific tools (imsg, peekaboo, Apple apps)
- Direct hardware access (camera, local screen)
- GUI applications (without X11 forwarding)
- Some system-level operations

### GPU in Docker

**NVIDIA:**
```bash
# Requires nvidia-container-toolkit
docker run --gpus all ...
```

**Apple Silicon:**
Not supported in Docker. Use native Ollama instead.

## Resource Requirements

Minimum specs by deployment type:

| Type | RAM | Storage | CPU | Notes |
|------|-----|---------|-----|-------|
| Minimal (cloud AI) | 1GB | 5GB | 1 core | Just gateway |
| Standard (cloud AI) | 2GB | 10GB | 2 cores | + Workspace |
| With Ollama (7B) | 8GB | 20GB | 4 cores | llama3.2:7b |
| With Ollama (32B) | 32GB | 50GB | 8 cores | qwen2.5-coder:32b |
| With Ollama (70B) | 64GB | 100GB | 16 cores | llama3.3:70b |

## Validation Function

```python
def validate_platform_compat(spec: dict, platform: dict) -> list[str]:
    """
    Returns list of errors/warnings for incompatible requests.
    
    platform = {
        "os": "darwin" | "linux" | "windows",
        "arch": "x86_64" | "arm64",
        "container": bool,
        "gpu": "nvidia" | "apple" | "amd" | None,
        "ram_gb": int,
        "pkg_manager": str,
    }
    """
    errors = []
    warnings = []
    
    # Check channels
    if "imessage" in spec.get("channels", {}) and platform["os"] != "darwin":
        errors.append("iMessage requires macOS")
    
    # Check skills
    macos_only_skills = ["imsg", "peekaboo", "apple-notes", "apple-reminders", "raycast"]
    for skill in spec.get("skills", {}).get("allowlist", []):
        if skill in macos_only_skills and platform["os"] != "darwin":
            errors.append(f"Skill '{skill}' requires macOS")
    
    # Check Ollama + GPU
    if spec.get("ai", {}).get("local", {}).get("enabled"):
        if platform["gpu"] == "nvidia" and platform["os"] == "darwin":
            errors.append("NVIDIA GPU not supported on macOS")
        if platform["container"] and platform["gpu"] == "apple":
            errors.append("Apple Silicon GPU not available in containers")
    
    # Check resources
    if spec.get("ai", {}).get("local", {}).get("models"):
        models = spec["ai"]["local"]["models"]
        if any("70b" in m.lower() for m in models):
            if platform.get("ram_gb", 0) < 64:
                warnings.append("70B models recommend 64GB+ RAM")
        elif any("32b" in m.lower() for m in models):
            if platform.get("ram_gb", 0) < 32:
                warnings.append("32B models recommend 32GB+ RAM")
    
    return errors, warnings
```
