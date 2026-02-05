#!/usr/bin/env python3
"""
Printify CLI - Manage print-on-demand products and orders.
"""

import argparse
import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://api.printify.com/v1"
TOKEN = os.environ.get("PRINTIFY_API_KEY", "")

def api_request(method, endpoint, data=None):
    """Make an API request to Printify."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "OpenClaw",
        "Content-Type": "application/json"
    }
    
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        error_body = e.read().decode()
        print(f"Error {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)

def cmd_shops(args):
    """List all shops."""
    shops = api_request("GET", "/shops.json")
    print(json.dumps(shops, indent=2))

def cmd_products(args):
    """List products in a shop."""
    endpoint = f"/shops/{args.shop}/products.json"
    if args.limit:
        endpoint += f"?limit={args.limit}"
    products = api_request("GET", endpoint)
    
    if args.compact:
        for p in products.get("data", []):
            status = "✓" if p.get("visible") else "○"
            print(f"{status} {p['id'][:8]}... | {p['title']}")
    else:
        print(json.dumps(products, indent=2))

def cmd_product(args):
    """Get a single product."""
    product = api_request("GET", f"/shops/{args.shop}/products/{args.product_id}.json")
    print(json.dumps(product, indent=2))

def cmd_orders(args):
    """List orders in a shop."""
    endpoint = f"/shops/{args.shop}/orders.json"
    if args.limit:
        endpoint += f"?limit={args.limit}"
    orders = api_request("GET", endpoint)
    
    if args.compact:
        for o in orders.get("data", []):
            status = o.get("status", "?")
            total = o.get("total_price", 0) / 100
            print(f"[{status}] {o['id'][:8]}... | ${total:.2f} | {o.get('address_to', {}).get('first_name', '?')}")
    else:
        print(json.dumps(orders, indent=2))

def cmd_order(args):
    """Get a single order."""
    order = api_request("GET", f"/shops/{args.shop}/orders/{args.order_id}.json")
    print(json.dumps(order, indent=2))

def cmd_uploads(args):
    """List uploaded images."""
    uploads = api_request("GET", "/uploads.json")
    
    if args.compact:
        for u in uploads.get("data", []):
            print(f"{u['id'][:8]}... | {u.get('file_name', 'unnamed')} | {u.get('width', '?')}x{u.get('height', '?')}")
    else:
        print(json.dumps(uploads, indent=2))

def cmd_catalog(args):
    """Browse the product catalog."""
    if args.blueprint_id:
        # Get specific blueprint
        bp = api_request("GET", f"/catalog/blueprints/{args.blueprint_id}.json")
        print(json.dumps(bp, indent=2))
    else:
        # List all blueprints
        blueprints = api_request("GET", "/catalog/blueprints.json")
        if args.compact:
            for bp in blueprints:
                print(f"{bp['id']} | {bp['title']}")
        else:
            print(json.dumps(blueprints, indent=2))

def cmd_providers(args):
    """List print providers for a blueprint."""
    if not args.blueprint_id:
        print("Error: --blueprint-id required", file=sys.stderr)
        sys.exit(1)
    providers = api_request("GET", f"/catalog/blueprints/{args.blueprint_id}/print_providers.json")
    
    if args.compact:
        for p in providers:
            print(f"{p['id']} | {p['title']}")
    else:
        print(json.dumps(providers, indent=2))

def cmd_upload(args):
    """Upload an image (URL-based)."""
    data = {
        "file_name": args.filename or os.path.basename(args.url),
        "url": args.url
    }
    result = api_request("POST", "/uploads/images.json", data)
    print(json.dumps(result, indent=2))

def cmd_publish(args):
    """Publish a product to the connected store."""
    data = {
        "title": True,
        "description": True,
        "images": True,
        "variants": True,
        "tags": True
    }
    result = api_request("POST", f"/shops/{args.shop}/products/{args.product_id}/publish.json", data)
    print(json.dumps(result, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Printify CLI")
    parser.add_argument("--shop", default=os.environ.get("PRINTIFY_SHOP_ID", "5182973"), 
                        help="Shop ID (default from PRINTIFY_SHOP_ID or 5182973)")
    
    subs = parser.add_subparsers(dest="command", required=True)
    
    # Shops
    subs.add_parser("shops", help="List all shops")
    
    # Products
    p_products = subs.add_parser("products", help="List products")
    p_products.add_argument("--limit", type=int, default=20)
    p_products.add_argument("--compact", "-c", action="store_true")
    
    p_product = subs.add_parser("product", help="Get a product")
    p_product.add_argument("product_id")
    
    # Orders
    p_orders = subs.add_parser("orders", help="List orders")
    p_orders.add_argument("--limit", type=int, default=20)
    p_orders.add_argument("--compact", "-c", action="store_true")
    
    p_order = subs.add_parser("order", help="Get an order")
    p_order.add_argument("order_id")
    
    # Uploads
    p_uploads = subs.add_parser("uploads", help="List uploads")
    p_uploads.add_argument("--compact", "-c", action="store_true")
    
    p_upload = subs.add_parser("upload", help="Upload image from URL")
    p_upload.add_argument("url")
    p_upload.add_argument("--filename", "-f")
    
    # Catalog
    p_catalog = subs.add_parser("catalog", help="Browse product catalog")
    p_catalog.add_argument("--blueprint-id", "-b", type=int)
    p_catalog.add_argument("--compact", "-c", action="store_true")
    
    p_providers = subs.add_parser("providers", help="List print providers")
    p_providers.add_argument("--blueprint-id", "-b", type=int, required=True)
    p_providers.add_argument("--compact", "-c", action="store_true")
    
    # Publish
    p_publish = subs.add_parser("publish", help="Publish product to store")
    p_publish.add_argument("product_id")
    
    args = parser.parse_args()
    
    if not TOKEN:
        print("Error: PRINTIFY_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    cmd_map = {
        "shops": cmd_shops,
        "products": cmd_products,
        "product": cmd_product,
        "orders": cmd_orders,
        "order": cmd_order,
        "uploads": cmd_uploads,
        "upload": cmd_upload,
        "catalog": cmd_catalog,
        "providers": cmd_providers,
        "publish": cmd_publish,
    }
    
    cmd_map[args.command](args)

if __name__ == "__main__":
    main()
