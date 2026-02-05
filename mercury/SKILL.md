---
name: mercury
description: "Mercury Bank: check balances, view transactions, list recipients via Mercury API."
metadata:
  openclaw:
    emoji: "🏦"
    requires:
      bins: ["python3"]
      env: ["MERCURY_API_KEY"]
---

# Mercury Bank Skill

Check balances, transactions, and recipients via the Mercury API.

## Setup

1. Get API key: https://mercury.com/settings/tokens
2. Set environment variable:
   ```bash
   export MERCURY_API_KEY="your-api-key"
   ```

## Commands

```bash
SCRIPT="python3 ~/.openclaw/skills/mercury/mercury.py"

# Quick balance check (all accounts)
$SCRIPT balance

# Recent transactions (all accounts)  
$SCRIPT recent --limit 20

# List all accounts
$SCRIPT accounts -c

# Get account details
$SCRIPT account <account_id> -c

# List transactions for an account
$SCRIPT transactions <account_id> -c --limit 50
$SCRIPT tx <account_id> --start 2026-01-01 --end 2026-01-31

# List recipients
$SCRIPT recipients -c
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `balance` / `bal` | Show balances for all accounts |
| `recent` | Recent transactions across all accounts |
| `accounts` | List all accounts |
| `account <id>` | Get account details (routing #, account #) |
| `transactions <id>` / `tx` | List transactions |
| `recipients` | List saved recipients |

## Read-Only

This skill is **read-only** — it can view data but cannot initiate payments or transfers. That requires additional API scopes and explicit confirmation flows.

## API Reference

https://docs.mercury.com/reference
