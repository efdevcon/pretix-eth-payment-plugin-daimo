# pretix_eth/x402/gas.py
"""Gas price caps (ported from relayer.ts lines 80-86) and balance asserts."""


class GasConditionError(Exception):
    pass


# Maximum gas price we're willing to pay (relayer subsidy), in gwei.
# Sourced from devcon src/services/relayer.ts GAS_PRICE_CAPS.
GAS_CAPS_GWEI = {
    1: 50.0,       # Ethereum mainnet
    10: 0.05,      # Optimism
    137: 500.0,    # Polygon
    8453: 0.13,    # Base
    42161: 0.3,    # Arbitrum
}

# Minimum relayer ETH balance (across all chains) to cover gas.
MIN_RELAYER_BALANCE_WEI = 10**14  # 0.0001 ETH


def assert_gas_conditions(*, w3, chain_id: int, relayer_addr: str) -> None:
    """Raise GasConditionError if gas is too high or relayer balance too low.
    Protects against runaway gas costs on the relayer wallet."""
    cap = GAS_CAPS_GWEI.get(chain_id)
    if cap is None:
        raise GasConditionError(f'No gas cap configured for chain {chain_id}')
    current_gwei = w3.eth.gas_price / 10**9
    if current_gwei > cap:
        raise GasConditionError(
            f'gas price {current_gwei:.4f} gwei exceeds cap {cap} gwei on chain {chain_id}',
        )
    bal = w3.eth.get_balance(relayer_addr)
    if bal < MIN_RELAYER_BALANCE_WEI:
        raise GasConditionError(
            f'relayer balance {bal} wei below minimum {MIN_RELAYER_BALANCE_WEI} on chain {chain_id}',
        )
