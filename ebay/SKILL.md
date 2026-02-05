---
name: ebay
description: "eBay selling integration: create listings, answer buyer questions, manage orders via eBay REST APIs."
metadata:
  openclaw:
    emoji: "🛒"
    requires:
      bins: ["python3"]
      env: ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_DEV_ID"]
---

# eBay Skill

Manage eBay selling operations via the official eBay REST APIs.

## Setup

1. Create eBay Developer account: https://developer.ebay.com
2. Create an application to get credentials
3. Set environment variables:
   ```bash
   export EBAY_CLIENT_ID="your-app-id"
   export EBAY_CLIENT_SECRET="your-cert-id"
   export EBAY_DEV_ID="your-dev-id"
   export EBAY_REDIRECT_URI="https://localhost:8080/callback"
   export EBAY_ENVIRONMENT="PRODUCTION"  # or SANDBOX
   ```
4. Run OAuth flow: `python3 ~/.openclaw/skills/ebay/oauth.py`

## Commands

### Listings
```bash
# List active listings
python3 ~/.openclaw/skills/ebay/ebay.py listings

# Create a listing
python3 ~/.openclaw/skills/ebay/ebay.py create --title "Item" --price 29.99 --condition NEW

# Update a listing
python3 ~/.openclaw/skills/ebay/ebay.py update <listing_id> --price 24.99
```

### Messages (Buyer Questions)
```bash
# Get unanswered messages
python3 ~/.openclaw/skills/ebay/ebay.py messages --unanswered

# Reply to a message
python3 ~/.openclaw/skills/ebay/ebay.py reply <message_id> "Your response here"
```

### Orders
```bash
# List recent orders
python3 ~/.openclaw/skills/ebay/ebay.py orders

# Get order details
python3 ~/.openclaw/skills/ebay/ebay.py order <order_id>

# Mark as shipped
python3 ~/.openclaw/skills/ebay/ebay.py ship <order_id> --tracking <number> --carrier USPS
```

## Token Management

Tokens are stored in `~/.ebay-tokens.json`. The skill auto-refreshes expired tokens.

## Status

🚧 **Pending Setup** — Awaiting eBay Developer credentials from user.
