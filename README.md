# Pretix WalletConnect Crypto Payment Plugin

A payment plugin for [Pretix](https://github.com/pretix/pretix) that accepts crypto payments via WalletConnect. No vendor dependency — payments are verified directly on-chain.

## Supported chains & tokens

- **Chains:** Ethereum, Optimism, Polygon, Base, Arbitrum
- **Tokens:** USDC (all chains), USDT0 (Optimism, Arbitrum), native ETH (all chains)

## How it works

1. Buyer selects "Crypto" at checkout and confirms the order
2. Pretix creates the order and redirects to the payment page
3. Buyer connects their wallet via WalletConnect (MetaMask, Rainbow, Coinbase Wallet, etc.)
4. Buyer picks a token and network, clicks "Pay now"
5. Plugin creates a quote (locked price, 10-min expiry) with a SIWE-lite signature challenge
6. Buyer signs the challenge (proves wallet ownership) then confirms the on-chain transfer
7. Plugin verifies the transaction on-chain via RPC (Alchemy or public fallback)
8. Order is marked as paid in Pretix

ETH pricing uses a dual-oracle system (Coinbase + Binance). If the two sources disagree by more than 5%, ETH payments are temporarily disabled and buyers are shown a notice to use USDC/USDT0 instead.

## Security

- Wallet ownership verified via signed challenge (SIWE-lite)
- Transaction hash is single-use (prevents cross-order replay)
- Chain, token contract, sender, recipient, and amount are all verified on-chain
- Quote expiry prevents stale-rate attacks
- Rate limiting on the verify endpoint

## Setup

### 1. Install

```bash
pip install -e 'git+https://github.com/efdevcon/pretix-eth-payment-plugin-daimo.git@wallet-connect#egg=pretix-eth-payment-plugin'
python -m pretix migrate pretix_eth
```

### 2. Configure

In Pretix admin, go to your event > Settings > Payment:

| Setting | Required | Description |
|---|---|---|
| Receive address | Yes | EIP-55 checksummed wallet address (same on all chains) |
| WalletConnect project ID | Yes | Free from [cloud.reown.com](https://cloud.reown.com) |
| Alchemy API key | No | Improves RPC reliability; falls back to public RPCs |
| Chain/token toggles | No | Enable/disable individual chains and tokens |
| Quote TTL | No | Default 600s (10 min) |
| Min confirmations | No | Default 1 |

### 3. Environment (optional)

| Variable | Purpose |
|---|---|
| `WC_ALCHEMY_API_KEY` | Overrides the plugin setting (preferred for production) |
| `WC_VERIFY_RATE_LIMIT_PER_MIN` | Verify endpoint rate limit per quote+IP (default 10) |

## Development

Requires Python 3.10+ and Node 20+.

```bash
git clone https://github.com/efdevcon/pretix-eth-payment-plugin-daimo.git
cd pretix-eth-payment-plugin-daimo
pip install -e '.[dev]'

# Build frontend
cd pretix_eth/static/wc_inject
pnpm install
pnpm run build   # or: pnpm run watch

# Run tests
cd ../../..
pytest tests/ -v
```

## History

This plugin evolved through multiple generations of Ethereum event ticketing:

- **2019** — Original ETH/DAI plugin for Ethereum Magicians Paris
- **DevCon5** — ERC-681 + Web3Modal support
- **DevCon6/LisCon** — Layer 2 support (first event with L2 payment option)
- **Devconnect IST** — WalletConnect, multi-network, automatic ETH rates
- **Devconnect 2025** — Rewritten to use Daimo Pay (any-chain checkout)
- **Devcon 8** — Replaced Daimo Pay with direct WalletConnect + on-chain verification (no vendor dependency)
