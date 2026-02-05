---
name: electrum
description: Manage Bitcoin wallet via Electrum CLI (create wallets, check balances, send/receive BTC, manage addresses, lightning payments). Use when user asks about Bitcoin, wallet balance, sending/receiving BTC, or cryptocurrency transactions.
---

# Electrum Bitcoin Wallet CLI

Command: `/Applications/Electrum.app/Contents/MacOS/run_electrum`

Requires Rosetta 2 on Apple Silicon.

## Daemon Mode

Most commands require the daemon running:

```bash
# Start daemon
electrum daemon -d

# Load wallet (after daemon starts)
electrum load_wallet

# Stop daemon
electrum stop
```

## Common Commands

### Wallet Management

```bash
# Create new wallet
electrum create

# Restore from seed
electrum restore "word1 word2 ... word12"

# Get wallet info
electrum getinfo

# List addresses
electrum listaddresses

# Create new receiving address
electrum createnewaddress
```

### Balance & History

```bash
# Get balance
electrum getbalance

# Transaction history
electrum onchain_history

# List unspent outputs
electrum listunspent
```

### Sending Bitcoin

```bash
# Create transaction
electrum payto <address> <amount_btc>

# Create and broadcast
electrum payto <address> <amount_btc> --broadcast

# Multi-output
electrum paytomany '{"addr1": 0.001, "addr2": 0.002}'
```

### Receiving

```bash
# Create payment request
electrum add_request <amount_btc> -m "memo"

# List requests
electrum listrequests
```

### Lightning (if enabled)

```bash
# Open channel
electrum open_channel <node_id> <amount_sat>

# Pay lightning invoice
electrum lnpay <bolt11_invoice>

# Create lightning invoice
electrum add_request <amount_btc> --lightning
```

## Network Options

```bash
--mainnet    # Default, real Bitcoin
--testnet    # Test network
--offline    # Offline mode
```

## Notes

- First run opens GUI to create/import wallet
- Use `-w /path/to/wallet` to specify wallet file
- Passwords prompted interactively when needed
- JSON output available for most commands
