# pretix_eth/x402/relayer.py
"""Python port of devcon src/services/relayer.ts — executes
transferWithAuthorization on behalf of the signing user, paying gas."""
import logging
from dataclasses import dataclass
from typing import Optional

from eth_account import Account
from web3 import Web3

from pretix_eth.chains import get_token_contract
from pretix_eth.rpc import get_rpc_url
from pretix_eth.x402.abi import USDC_ABI
from pretix_eth.x402.gas import assert_gas_conditions
from pretix_eth.x402.signatures import (
    is_smart_wallet_signature, split_eoa_signature, unwrap_erc6492,
)

log = logging.getLogger(__name__)


class RelayerError(Exception):
    pass


@dataclass
class RelayerResult:
    tx_hash: str
    chain_id: int


def _get_w3(chain_id: int, settings_key: Optional[str]) -> Web3:
    url = get_rpc_url(chain_id, settings_key=settings_key)
    return Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 30}))


def _get_relayer_account(pk: str):
    return Account.from_key(pk)


def execute_transfer_with_authorization(
    *,
    chain_id: int,
    symbol: str,
    authorization: dict,
    signature: str,
    relayer_pk: str,
    alchemy_key: Optional[str],
) -> RelayerResult:
    """Broadcast transferWithAuthorization to the token contract.
    Handles both EOA (v/r/s split) and smart-wallet (bytes overload + 6492 unwrap) signatures.

    `authorization` must contain: from, to, value, validAfter, validBefore, nonce.
    """
    if not relayer_pk:
        raise RelayerError('Relayer private key not configured')

    contract_info = get_token_contract(chain_id, symbol)
    if contract_info is None:
        raise RelayerError(f'No contract for {symbol} on chain {chain_id}')
    token_address = Web3.to_checksum_address(contract_info['address'])

    w3 = _get_w3(chain_id, alchemy_key)
    account = _get_relayer_account(relayer_pk)

    # 1. Gas price + relayer balance guard
    assert_gas_conditions(w3=w3, chain_id=chain_id, relayer_addr=account.address)

    contract = w3.eth.contract(address=token_address, abi=USDC_ABI)

    # 2. Nonce already used?
    nonce_bytes = bytes.fromhex(authorization['nonce'][2:])
    auth_used = contract.functions.authorizationState(
        Web3.to_checksum_address(authorization['from']),
        nonce_bytes,
    ).call()
    if auth_used:
        raise RelayerError('authorization nonce already used on-chain')

    # 3. Payer has balance?
    payer_balance = contract.functions.balanceOf(
        Web3.to_checksum_address(authorization['from']),
    ).call()
    required = int(authorization['value'])
    if payer_balance < required:
        raise RelayerError(f'insufficient payer balance: have {payer_balance}, need {required}')

    # 4. Build + sign + broadcast
    unwrapped_sig = unwrap_erc6492(signature)

    if is_smart_wallet_signature(signature):
        # Smart wallet: use bytes overload, keep the ERC-6492 wrapper (the contract
        # may need to deploy the wallet first via the factory embedded in it).
        call = contract.functions.transferWithAuthorization(
            Web3.to_checksum_address(authorization['from']),
            Web3.to_checksum_address(authorization['to']),
            int(authorization['value']),
            int(authorization['validAfter']),
            int(authorization['validBefore']),
            nonce_bytes,
            bytes.fromhex(signature[2:]),
        )
    else:
        parts = split_eoa_signature(unwrapped_sig)
        call = contract.functions.transferWithAuthorization(
            Web3.to_checksum_address(authorization['from']),
            Web3.to_checksum_address(authorization['to']),
            int(authorization['value']),
            int(authorization['validAfter']),
            int(authorization['validBefore']),
            nonce_bytes,
            parts['v'],
            bytes.fromhex(parts['r'][2:]),
            bytes.fromhex(parts['s'][2:]),
        )

    tx = call.build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'chainId': chain_id,
    })
    signed = account.sign_transaction(tx)
    raw = getattr(signed, 'raw_transaction', None) or signed.rawTransaction
    tx_hash_bytes = w3.eth.send_raw_transaction(raw)
    return RelayerResult(tx_hash='0x' + tx_hash_bytes.hex(), chain_id=chain_id)
