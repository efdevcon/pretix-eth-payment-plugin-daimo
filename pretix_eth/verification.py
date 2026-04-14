"""On-chain verification for ERC-20 Transfer and native ETH sends."""
import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

# keccak256("Transfer(address,address,uint256)")
ERC20_TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'


@dataclass
class VerificationResult:
    verified: bool
    block_number: Optional[int] = None
    confirmed_at: Optional[int] = None
    error: Optional[str] = None


def _normalize_hex(val) -> str:
    """Convert HexBytes / bytes / str to a lowercase 0x-prefixed hex string."""
    if hasattr(val, 'hex'):
        val = val.hex()
    s = str(val).lower()
    if not s.startswith('0x'):
        s = '0x' + s
    return s


def _addr_eq(a, b) -> bool:
    return _normalize_hex(a) == _normalize_hex(b)


def _topic_to_addr(topic) -> str:
    # 32-byte topic → last 20 bytes as 0x-prefixed hex
    h = _normalize_hex(topic)  # '0x' + 64 hex chars
    return '0x' + h[-40:]


def verify_erc20_transfer(*, w3, chain_id: int, tx_hash: str,
                          expected_from: str, expected_to: str,
                          expected_token: str, expected_amount: int,
                          min_confirmations: int = 1) -> VerificationResult:
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        return VerificationResult(False, error=f'RPC error: {e}')

    if receipt is None:
        return VerificationResult(False, error='tx not mined yet')

    if receipt.get('status') != 1:
        return VerificationResult(False, error='tx reverted on-chain')

    block = receipt.get('blockNumber')
    head = w3.eth.block_number
    if head - block < min_confirmations:
        return VerificationResult(
            False, error=f'insufficient confirmations ({head - block}/{min_confirmations})',
        )

    # Find matching Transfer log
    for log_entry in receipt.get('logs', []):
        if not _addr_eq(log_entry.get('address', ''), expected_token):
            continue
        topics = log_entry.get('topics', [])
        if len(topics) < 3:
            continue
        if _normalize_hex(topics[0]) != ERC20_TRANSFER_TOPIC:
            continue
        t_from = _topic_to_addr(topics[1])
        t_to = _topic_to_addr(topics[2])
        if not _addr_eq(t_from, expected_from):
            continue
        if not _addr_eq(t_to, expected_to):
            continue
        data_hex = _normalize_hex(log_entry.get('data', '0x0'))[2:]  # strip 0x
        value = int(data_hex, 16) if data_hex else 0
        if value < expected_amount:
            return VerificationResult(False, error=f'amount too low: {value} < {expected_amount}')
        return VerificationResult(True, block_number=block)

    return VerificationResult(False, error='no matching transfer found in tx')


def verify_native_eth(*, w3, tx_hash: str, expected_from: str,
                      expected_to: str, expected_amount_wei: int,
                      min_confirmations: int = 1) -> VerificationResult:
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        tx = w3.eth.get_transaction(tx_hash)
    except Exception as e:
        return VerificationResult(False, error=f'RPC error: {e}')

    if receipt is None or tx is None:
        return VerificationResult(False, error='tx not mined yet')

    if receipt.get('status') != 1:
        return VerificationResult(False, error='tx reverted on-chain')

    block = receipt.get('blockNumber')
    head = w3.eth.block_number
    if head - block < min_confirmations:
        return VerificationResult(
            False, error=f'insufficient confirmations ({head - block}/{min_confirmations})',
        )

    if not _addr_eq(tx.get('from', ''), expected_from):
        return VerificationResult(False, error='tx sender mismatch')
    if not _addr_eq(tx.get('to', ''), expected_to):
        return VerificationResult(False, error='tx recipient mismatch')
    if int(tx.get('value', 0)) < expected_amount_wei:
        return VerificationResult(False, error='tx value too low')

    return VerificationResult(True, block_number=block)
