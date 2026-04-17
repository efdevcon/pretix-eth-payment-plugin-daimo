from unittest import mock
import pytest
from pretix_eth.x402.balances import fetch_balances_for_wallet


def test_fetch_balances_uses_correct_rpc(monkeypatch):
    def fake_get_rpc(chain_id, settings_key):
        return f'https://fake-rpc-{chain_id}'
    monkeypatch.setattr('pretix_eth.x402.balances.get_rpc_url', fake_get_rpc)

    # Mock Web3 client
    fake_web3 = mock.MagicMock()
    fake_web3.eth.get_balance.return_value = 5 * 10**17  # 0.5 ETH
    fake_contract = mock.MagicMock()
    fake_contract.functions.balanceOf.return_value.call.return_value = 50 * 10**6  # 50 USDC
    fake_web3.eth.contract.return_value = fake_contract
    monkeypatch.setattr('pretix_eth.x402.balances.Web3', mock.MagicMock(return_value=fake_web3))

    result = fetch_balances_for_wallet(
        wallet='0x' + '1' * 40, chain_ids=[8453], alchemy_key=None,
    )
    assert len(result) > 0
    eth_entry = next((e for e in result if e['symbol'] == 'ETH'), None)
    assert eth_entry is not None
    assert eth_entry['balance'] == str(5 * 10**17)
