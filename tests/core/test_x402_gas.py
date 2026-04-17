# tests/core/test_x402_gas.py
from unittest import mock
import pytest
from pretix_eth.x402.gas import GAS_CAPS_GWEI, assert_gas_conditions, GasConditionError


def test_gas_caps_defined_for_all_chains():
    for cid in [1, 10, 137, 8453, 42161]:
        assert cid in GAS_CAPS_GWEI
        assert GAS_CAPS_GWEI[cid] > 0


def test_gas_too_high_raises():
    w3 = mock.MagicMock()
    w3.eth.gas_price = 5 * 10**9  # 5 gwei
    w3.eth.get_balance.return_value = 10**18
    with pytest.raises(GasConditionError, match='gas price'):
        # Base cap is 0.13 gwei — 5 gwei exceeds it
        assert_gas_conditions(w3=w3, chain_id=8453, relayer_addr='0x' + '1' * 40)


def test_gas_ok_and_balance_ok():
    w3 = mock.MagicMock()
    w3.eth.gas_price = 10**8  # 0.1 gwei (under 0.13 cap for Base)
    w3.eth.get_balance.return_value = 10**18
    # Should not raise
    assert_gas_conditions(w3=w3, chain_id=8453, relayer_addr='0x' + '1' * 40)


def test_low_relayer_balance_raises():
    w3 = mock.MagicMock()
    w3.eth.gas_price = 10**8
    w3.eth.get_balance.return_value = 0
    with pytest.raises(GasConditionError, match='balance'):
        assert_gas_conditions(w3=w3, chain_id=8453, relayer_addr='0x' + '1' * 40)
