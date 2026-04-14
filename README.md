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

It started with [ligi](https://github.com/ligi) suggesting [pretix for Ethereum
Magicians](https://ethereum-magicians.org/t/charging-for-tickets-participant-numbers-event-ticketing-for-council-of-paris-2019/2321/2).

Then it was used for Ethereum Magicians in Paris (shout out to
[boris](https://github.com/bmann) for making this possible) - but accepting ETH
or DAI was a fully manual process there.

Afterwards boris [put up some funds for a gitcoin
bounty](https://github.com/spadebuilders/community/issues/30) to make a plugin
that automates this process. And [nanexcool](https://github.com/nanexcool)
increased the funds and added the requirement for DAI.

The initial version was developed by [vic-en](https://github.com/vic-en) but he
vanished from the project after cashing in the bounty money and left the plugin
in a non-working state.

Then the idea came up to use this plugin for DevCon5 and the plugin was forked
to this repo and [david sanders](https://github.com/davesque), [piper
merriam](https://github.com/pipermerriam), [rami](https://github.com/raphaelm),
[Pedro Gomes](https://github.com/pedrouid), and [Jamie
Pitts](https://github.com/jpitts) brought it to a state where it is usable for
DevCon5 (still a lot of work to be done to make this a good plugin). Currently,
it is semi-automatic. But it now has ERC-681 and Web3Modal
support. If you want to dig a bit into the problems that emerged short before
the launch you can have a look at [this
issue](https://github.com/esPass/pretix-eth-payment-plugin/pull/49)

For DEVcon6 the plugin was extended with some more features like [Layer2 support by Rahul](https://github.com/rahul-kothari). Layer2 will play a significant [role in Ethereum](https://ethereum-magicians.org/t/a-rollup-centric-ethereum-roadmap/4698). Unfortunately DEVcon6 was delayed due to covid - but we where able to use and this way test via the [LisCon](https://liscon.org) ticket sale. As far as we know this was the first event ever offering a Layer2 payment option.
In the process tooling like [Web3Modal](https://github.com/Web3Modal/web3modal/) / [Checkout](https://github.com/Web3Modal/web3modal-checkout) that we depend on was improved.

For Devconnect IST an effort was made to improve the plugin in a variety of ways: WalletConnect support, single receiver mode (accept payments using just one wallet), more networks, automatic ETH rate fetching, improved UI and messaging, and smart contract wallet support. All of these features made it into this version of the plugin, except for smart contract wallet support - issues processing transactions stemming from sc wallets meant that we ultimately had to turn away sc wallet payments altogether.

For Devconnect 2025, the plugin was rewritten to use [Daimo Pay](https://pay.daimo.com), providing any-chain checkout and automatic refunds. See [DIP-64](https://forum.devcon.org/t/dip-64-universal-checkout-for-devcon-nect/5346).

For Devcon 8, Daimo Pay was replaced with direct WalletConnect + on-chain verification, removing all vendor dependencies. Payments are now verified directly via RPC with a SIWE-lite challenge for wallet ownership proof.
