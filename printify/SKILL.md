---
name: printify
description: "Printify print-on-demand: list products, orders, catalog, upload designs, publish to store."
metadata:
  openclaw:
    emoji: "🎨"
    requires:
      bins: ["python3"]
      env: ["PRINTIFY_API_KEY"]
---

# Printify Skill

Manage print-on-demand products via the Printify API.

## Setup

```bash
export PRINTIFY_API_KEY="your-token"
export PRINTIFY_SHOP_ID="5182973"  # Optional, defaults to Mike's shop
```

## Commands

```bash
SCRIPT="python3 ~/.openclaw/skills/printify/printify.py"

# List shops
$SCRIPT shops

# List products (compact view)
$SCRIPT products -c

# Get product details
$SCRIPT product <product_id>

# List orders
$SCRIPT orders -c

# Get order details
$SCRIPT order <order_id>

# Browse catalog (all blueprints)
$SCRIPT catalog -c

# Get blueprint details
$SCRIPT catalog -b 145  # e.g., Unisex Heavy Cotton Tee

# List print providers for a blueprint
$SCRIPT providers -b 145 -c

# List uploaded images
$SCRIPT uploads -c

# Upload image from URL
$SCRIPT upload "https://example.com/design.png" -f "my-design.png"

# Publish product to connected store
$SCRIPT publish <product_id>
```

## Shop Info

- **Shop ID:** 5182973
- **Name:** mikeharwitz
- **Channel:** Shopify

## Rate Limits

- 600 requests/min global
- 100 requests/min for catalog endpoints
- 200 product publishes per 30 min

## API Reference

https://developers.printify.com/
