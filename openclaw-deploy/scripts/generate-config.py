#!/usr/bin/env python3
"""
Generate OpenClaw configuration from deployment parameters.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Generate OpenClaw configuration")
    parser.add_argument("--output", "-o", required=True, help="Output config file path")
    parser.add_argument("--env-output", help="Output .env file path")
    parser.add_argument("--ai-primary", help="Primary AI model")
    parser.add_argument("--ai-fallback", help="Fallback AI model(s), comma-separated")
    parser.add_argument("--local-ai", action="store_true", help="Enable Ollama")
    parser.add_argument("--local-models", default="llama3.3", help="Ollama models")
    parser.add_argument("--channels", help="Enabled channels, comma-separated")
    parser.add_argument("--domain", help="Domain for webhooks/SSL")
    parser.add_argument("--port", type=int, default=18789, help="Gateway port")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--spec", help="Load from spec file")
    return parser.parse_args()


def load_spec(spec_file: str) -> dict:
    """Load configuration from spec file."""
    with open(spec_file) as f:
        content = f.read()
    # Handle JSON5 (strip comments, trailing commas)
    # Simple approach: try json first, then strip // comments
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        import re
        # Remove // comments
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # Remove trailing commas
        content = re.sub(r",\s*([}\]])", r"\1", content)
        return json.loads(content)


def generate_config(args) -> tuple[dict, dict]:
    """Generate config dict and env vars dict."""
    
    config = {
        "gateway": {
            "port": args.port,
        },
        "agents": {
            "defaults": {
                "workspace": "~/.openclaw/workspace",
            }
        },
        "channels": {},
    }
    
    env_vars = {}
    
    # Load spec if provided
    if args.spec:
        spec = load_spec(args.spec)
        # Merge spec into config
        deep_merge(config, spec_to_config(spec))
        env_vars.update(spec_to_env(spec))
    
    # AI configuration
    if args.ai_primary:
        config.setdefault("agents", {}).setdefault("defaults", {})["model"] = {
            "primary": args.ai_primary
        }
        
        # Add env var hint
        provider = args.ai_primary.split("/")[0]
        env_vars[f"{provider.upper()}_API_KEY"] = f"<your-{provider}-api-key>"
    
    if args.ai_fallback:
        fallbacks = [f.strip() for f in args.ai_fallback.split(",")]
        config["agents"]["defaults"]["model"]["fallbacks"] = fallbacks
        
        # Add env var hints for fallback providers
        for fb in fallbacks:
            provider = fb.split("/")[0]
            if provider == "ollama":
                env_vars["OLLAMA_API_KEY"] = "ollama-local"
            else:
                key = f"{provider.upper()}_API_KEY"
                if key not in env_vars:
                    env_vars[key] = f"<your-{provider}-api-key>"
    
    # Local AI (Ollama)
    if args.local_ai:
        env_vars["OLLAMA_API_KEY"] = "ollama-local"
    
    # Channels
    if args.channels:
        channels = [c.strip().lower() for c in args.channels.split(",")]
        
        for channel in channels:
            if channel == "whatsapp":
                config["channels"]["whatsapp"] = {
                    "dmPolicy": "pairing",
                    "groups": {"*": {"requireMention": True}}
                }
            
            elif channel == "telegram":
                config["channels"]["telegram"] = {
                    "enabled": True,
                    "dmPolicy": "pairing",
                    "groups": {"*": {"requireMention": True}}
                }
                env_vars["TELEGRAM_BOT_TOKEN"] = "<your-telegram-bot-token>"
            
            elif channel == "discord":
                config["channels"]["discord"] = {
                    "enabled": True,
                    "dm": {"enabled": True, "policy": "pairing"},
                    "guilds": {}
                }
                env_vars["DISCORD_BOT_TOKEN"] = "<your-discord-bot-token>"
            
            elif channel == "slack":
                config["channels"]["slack"] = {
                    "enabled": True,
                    "dm": {"enabled": True, "policy": "pairing"},
                    "channels": {}
                }
                env_vars["SLACK_BOT_TOKEN"] = "<your-slack-bot-token>"
                env_vars["SLACK_APP_TOKEN"] = "<your-slack-app-token>"
            
            elif channel == "signal":
                config["channels"]["signal"] = {
                    "enabled": True,
                    "dmPolicy": "pairing",
                    "groupPolicy": "allowlist"
                }
            
            elif channel == "imessage":
                config["channels"]["imessage"] = {
                    "enabled": True,
                    "dmPolicy": "pairing"
                }
            
            elif channel == "googlechat":
                config["channels"]["googlechat"] = {
                    "enabled": True,
                    "dm": {"enabled": True, "policy": "pairing"}
                }
    
    # Domain/SSL
    if args.domain:
        # For webhook-based channels, set the URL
        if "telegram" in config.get("channels", {}):
            config["channels"]["telegram"]["webhookUrl"] = f"https://{args.domain}/telegram-webhook"
            config["channels"]["telegram"]["webhookPath"] = "/telegram-webhook"
        
        if "googlechat" in config.get("channels", {}):
            config["channels"]["googlechat"]["audience"] = f"https://{args.domain}/googlechat"
            config["channels"]["googlechat"]["webhookPath"] = "/googlechat"
    
    return config, env_vars


def spec_to_config(spec: dict) -> dict:
    """Convert deployment spec to OpenClaw config format."""
    config = {}
    
    # AI
    if "ai" in spec:
        ai = spec["ai"]
        model_config = {}
        if "primary" in ai:
            model_config["primary"] = ai["primary"]
        if "fallbacks" in ai:
            model_config["fallbacks"] = ai["fallbacks"]
        if model_config:
            config.setdefault("agents", {}).setdefault("defaults", {})["model"] = model_config
    
    # Identity
    if "identity" in spec:
        identity = spec["identity"]
        config.setdefault("agents", {}).setdefault("list", [{}])[0]["identity"] = {
            "name": identity.get("name", "Assistant"),
            "emoji": identity.get("emoji", "🤖"),
            "theme": identity.get("theme", "")
        }
    
    # Network
    if "network" in spec:
        net = spec["network"]
        config.setdefault("gateway", {})["port"] = net.get("port", 18789)
    
    # Sandbox
    if "sandbox" in spec:
        sb = spec["sandbox"]
        config.setdefault("agents", {}).setdefault("defaults", {})["sandbox"] = {
            "mode": sb.get("mode", "non-main"),
            "scope": sb.get("scope", "agent")
        }
    
    # Channels
    if "channels" in spec:
        for channel, settings in spec["channels"].items():
            if settings.get("enabled", False):
                config.setdefault("channels", {})[channel] = {"enabled": True}
    
    return config


def spec_to_env(spec: dict) -> dict:
    """Extract env vars from spec."""
    env = {}
    
    if "ai" in spec:
        ai = spec["ai"]
        if "primary" in ai:
            provider = ai["primary"].split("/")[0]
            env[f"{provider.upper()}_API_KEY"] = f"<your-{provider}-api-key>"
        
        if ai.get("local", {}).get("enabled"):
            env["OLLAMA_API_KEY"] = "ollama-local"
    
    return env


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge override into base."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base


def format_json5(config: dict) -> str:
    """Format config as JSON5 (with comments for placeholders)."""
    output = json.dumps(config, indent=2)
    # Add comment hints for placeholder values
    lines = output.split("\n")
    result = []
    for line in lines:
        if "<your-" in line and "-api-key>" in line:
            # Add comment
            result.append(line.rstrip(",") + "  // TODO: Replace with actual key" + ("," if line.rstrip().endswith(",") else ""))
        else:
            result.append(line)
    return "\n".join(result)


def format_env(env_vars: dict) -> str:
    """Format env vars as .env file."""
    lines = ["# OpenClaw Environment Variables", "# Generated by openclaw-deploy", ""]
    
    for key, value in sorted(env_vars.items()):
        if value.startswith("<"):
            lines.append(f"# {key}={value}  # TODO: Replace with actual value")
        else:
            lines.append(f"{key}={value}")
    
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    
    config, env_vars = generate_config(args)
    
    # Write config
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write(format_json5(config))
    
    print(f"✓ Config written to: {output_path}")
    
    # Write env file
    if args.env_output:
        env_path = Path(args.env_output)
        with open(env_path, "w") as f:
            f.write(format_env(env_vars))
        print(f"✓ Env file written to: {env_path}")
    
    # Print summary
    print("\nConfiguration Summary:")
    print(f"  Port: {args.port}")
    if args.ai_primary:
        print(f"  Primary AI: {args.ai_primary}")
    if args.ai_fallback:
        print(f"  Fallback AI: {args.ai_fallback}")
    if args.local_ai:
        print(f"  Local AI: Ollama ({args.local_models})")
    if args.channels:
        print(f"  Channels: {args.channels}")
    if args.domain:
        print(f"  Domain: {args.domain}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
