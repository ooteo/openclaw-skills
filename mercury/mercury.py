#!/usr/bin/env python3
"""
Mercury Bank CLI - Check balances, transactions, recipients, and payments.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://api.mercury.com/api/v1"
TOKEN = os.environ.get("MERCURY_API_KEY", "")


def api_request(method, endpoint, data=None):
    """Make an API request to Mercury."""
    url = f"{API_BASE}{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mercury-CLI/1.0 (OpenClaw)"
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


def format_currency(amount):
    """Format amount as dollars."""
    return f"${amount:,.2f}"


def cmd_accounts(args):
    """List all accounts."""
    result = api_request("GET", "/accounts")
    accounts = result.get("accounts", [])
    
    if args.compact:
        for acc in accounts:
            balance = format_currency(acc.get("currentBalance", 0))
            print(f"{acc.get('name', 'Unnamed')} | {acc['id'][:8]}... | {balance}")
    else:
        print(json.dumps(accounts, indent=2))


def cmd_account(args):
    """Get single account details."""
    result = api_request("GET", f"/account/{args.account_id}")
    
    if args.compact:
        acc = result
        print(f"Name: {acc.get('name', 'Unnamed')}")
        print(f"ID: {acc['id']}")
        print(f"Type: {acc.get('type', '?')}")
        print(f"Routing: {acc.get('routingNumber', '?')}")
        print(f"Account #: {acc.get('accountNumber', '?')}")
        print(f"Balance: {format_currency(acc.get('currentBalance', 0))}")
        print(f"Available: {format_currency(acc.get('availableBalance', 0))}")
    else:
        print(json.dumps(result, indent=2))


def cmd_transactions(args):
    """List transactions."""
    params = []
    if args.limit:
        params.append(f"limit={args.limit}")
    if args.offset:
        params.append(f"offset={args.offset}")
    if args.start:
        params.append(f"start={args.start}")
    if args.end:
        params.append(f"end={args.end}")
    
    query = f"?{'&'.join(params)}" if params else ""
    result = api_request("GET", f"/account/{args.account_id}/transactions{query}")
    transactions = result.get("transactions", [])
    
    if args.compact:
        for tx in transactions:
            amount = format_currency(abs(tx.get("amount", 0)))
            sign = "+" if tx.get("amount", 0) > 0 else "-"
            date = tx.get("postedAt", tx.get("createdAt", "?"))[:10]
            desc = tx.get("bankDescription", tx.get("externalMemo", "?"))[:40]
            status = tx.get("status", "?")
            print(f"{date} | {sign}{amount:>12} | [{status}] {desc}")
    else:
        print(json.dumps(transactions, indent=2))


def cmd_recipients(args):
    """List recipients."""
    result = api_request("GET", "/recipients")
    recipients = result.get("recipients", [])
    
    if args.compact:
        for r in recipients:
            name = r.get("name", "Unnamed")
            rtype = r.get("paymentMethod", "?")
            print(f"{r['id'][:8]}... | {name} | {rtype}")
    else:
        print(json.dumps(recipients, indent=2))


def cmd_balance(args):
    """Quick balance check for all accounts."""
    result = api_request("GET", "/accounts")
    accounts = result.get("accounts", [])
    
    total = 0
    for acc in accounts:
        balance = acc.get("currentBalance", 0)
        total += balance
        print(f"{acc.get('name', 'Unnamed')}: {format_currency(balance)}")
    
    if len(accounts) > 1:
        print(f"---")
        print(f"Total: {format_currency(total)}")


def cmd_recent(args):
    """Show recent transactions across all accounts."""
    accounts_result = api_request("GET", "/accounts")
    accounts = accounts_result.get("accounts", [])
    
    all_transactions = []
    for acc in accounts:
        tx_result = api_request("GET", f"/account/{acc['id']}/transactions?limit={args.limit}")
        for tx in tx_result.get("transactions", []):
            tx["_account"] = acc.get("name", "Unnamed")
            all_transactions.append(tx)
    
    # Sort by date
    all_transactions.sort(key=lambda x: x.get("postedAt", x.get("createdAt", "")), reverse=True)
    
    for tx in all_transactions[:args.limit]:
        amount = format_currency(abs(tx.get("amount", 0)))
        sign = "+" if tx.get("amount", 0) > 0 else "-"
        date = tx.get("postedAt", tx.get("createdAt", "?"))[:10]
        desc = tx.get("bankDescription", tx.get("externalMemo", "?"))[:35]
        acc_name = tx["_account"][:10]
        print(f"{date} | {acc_name:>10} | {sign}{amount:>12} | {desc}")


def main():
    parser = argparse.ArgumentParser(description="Mercury Bank CLI")
    subs = parser.add_subparsers(dest="command", required=True)
    
    # Accounts
    p_accounts = subs.add_parser("accounts", help="List all accounts")
    p_accounts.add_argument("--compact", "-c", action="store_true")
    
    p_account = subs.add_parser("account", help="Get account details")
    p_account.add_argument("account_id")
    p_account.add_argument("--compact", "-c", action="store_true")
    
    # Transactions
    p_tx = subs.add_parser("transactions", aliases=["tx"], help="List transactions")
    p_tx.add_argument("account_id")
    p_tx.add_argument("--limit", type=int, default=25)
    p_tx.add_argument("--offset", type=int)
    p_tx.add_argument("--start", help="Start date (YYYY-MM-DD)")
    p_tx.add_argument("--end", help="End date (YYYY-MM-DD)")
    p_tx.add_argument("--compact", "-c", action="store_true")
    
    # Recipients
    p_recipients = subs.add_parser("recipients", help="List recipients")
    p_recipients.add_argument("--compact", "-c", action="store_true")
    
    # Quick commands
    p_balance = subs.add_parser("balance", aliases=["bal"], help="Quick balance check")
    
    p_recent = subs.add_parser("recent", help="Recent transactions (all accounts)")
    p_recent.add_argument("--limit", type=int, default=15)
    
    args = parser.parse_args()
    
    if not TOKEN:
        print("Error: MERCURY_API_KEY not set", file=sys.stderr)
        print("Get your API key at: https://mercury.com/settings/tokens", file=sys.stderr)
        sys.exit(1)
    
    cmd_map = {
        "accounts": cmd_accounts,
        "account": cmd_account,
        "transactions": cmd_transactions,
        "tx": cmd_transactions,
        "recipients": cmd_recipients,
        "balance": cmd_balance,
        "bal": cmd_balance,
        "recent": cmd_recent,
    }
    
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
