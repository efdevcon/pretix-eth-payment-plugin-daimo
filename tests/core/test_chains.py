import pytest
from pretix_eth.chains import (
    SUPPORTED_CHAINS, TOKEN_CONTRACTS, CHAIN_METADATA,
    get_token_contract, is_supported,
)


def test_all_five_chains_present():
    assert SUPPORTED_CHAINS == [1, 10, 137, 8453, 42161]


def test_base_usdc_contract():
    c = get_token_contract(8453, 'USDC')
    assert c['address'].lower() == '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
    assert c['decimals'] == 6


def test_is_supported_rejects_unknown_combo():
    assert is_supported(1, 'USDC') is True
    assert is_supported(999, 'USDC') is False
    assert is_supported(1, 'DAI') is False


def test_usdt0_only_on_optimism_and_arbitrum():
    # USD₮0 is Tether's OFT, only live on Optimism + Arbitrum.
    assert is_supported(10, 'USDT0') is True
    assert is_supported(42161, 'USDT0') is True
    # Not available elsewhere
    assert is_supported(1, 'USDT0') is False
    assert is_supported(137, 'USDT0') is False
    assert is_supported(8453, 'USDT0') is False


def test_eth_supported_on_all_chains():
    for cid in SUPPORTED_CHAINS:
        assert is_supported(cid, 'ETH') is True


def test_chain_metadata_has_explorer_for_base():
    meta = CHAIN_METADATA[8453]
    assert 'basescan.org' in meta['explorer_url']
    assert meta['name'] == 'Base'
