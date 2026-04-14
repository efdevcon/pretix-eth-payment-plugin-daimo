import { useState } from 'react'
import {
  useAccount,
  useSwitchChain,
  useWriteContract,
  useSendTransaction,
} from 'wagmi'
import { erc20Abi } from 'viem'
import type { WCConfig } from '../config'
import type { Quote } from '../WCPaymentApp'

const MAX_VERIFY_ATTEMPTS = 5

type Status =
  | 'idle'
  | 'switching'
  | 'signing'
  | 'verifying'
  | 'error'

const RETRYABLE_ERROR_SUBSTRINGS = [
  'tx not mined yet',
  'insufficient confirmations',
]

function parseOrgAndEvent(): { organizer: string; event: string } {
  const match = window.location.pathname.match(/^\/([^/]+)\/([^/]+)/)
  if (!match) throw new Error('Could not parse organizer/event from URL')
  return { organizer: match[1], event: match[2] }
}

function formatAmount(q: Quote): string {
  if (q.symbol === 'ETH') {
    const wei = BigInt(q.amount_raw)
    // Show 6 decimals of ETH precision
    const eth = Number(wei) / 1e18
    return `${eth.toFixed(6)} ETH`
  }
  // USDC / USDT0: 6 decimals, render as $XX.YY
  const raw = BigInt(q.amount_raw)
  const usd = Number(raw) / 1e6
  return `${usd.toFixed(2)} ${q.symbol}`
}

export function PayStep({
  config,
  quote,
  onConfirmed,
}: {
  config: WCConfig
  quote: Quote
  onConfirmed: (txHash: string) => void
}) {
  const [status, setStatus] = useState<Status>('idle')
  const [error, setError] = useState<string | null>(null)
  const account = useAccount()
  const { switchChainAsync } = useSwitchChain()
  const { writeContractAsync } = useWriteContract()
  const { sendTransactionAsync } = useSendTransaction()

  async function pollVerify(txHash: string) {
    const { organizer, event } = parseOrgAndEvent()
    for (let attempt = 0; attempt < MAX_VERIFY_ATTEMPTS; attempt++) {
      // Exponential backoff: 1s, 2s, 4s, 8s, 16s
      const delayMs = 1000 * Math.pow(2, attempt)
      await new Promise((r) => setTimeout(r, delayMs))

      const r = await fetch(`${config.urlPrefix}/verify/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          quote_id: quote.quote_id,
          tx_hash: txHash,
          chain_id: quote.chain_id,
          organizer,
          event,
        }),
      })

      if (r.ok) {
        const body = await r.json()
        if (body.verified) return
      } else {
        const body = await r.json().catch(() => ({}))
        const errMsg = (body.error as string | undefined) || `verify HTTP ${r.status}`
        const isRetryable = RETRYABLE_ERROR_SUBSTRINGS.some((s) =>
          errMsg.includes(s),
        )
        if (!isRetryable) {
          throw new Error(errMsg)
        }
      }
    }
    throw new Error('Verification timed out; please check your transaction and refresh.')
  }

  async function handlePay() {
    setError(null)
    try {
      // Switch chain if needed
      if (account.chainId !== quote.chain_id) {
        setStatus('switching')
        await switchChainAsync({ chainId: quote.chain_id })
      }

      setStatus('signing')
      let txHash: string
      if (quote.symbol === 'ETH') {
        txHash = await sendTransactionAsync({
          to: quote.receive_address as `0x${string}`,
          value: BigInt(quote.amount_raw),
          chainId: quote.chain_id,
        })
      } else {
        if (!quote.token_address) {
          throw new Error('token_address missing for stablecoin quote')
        }
        txHash = await writeContractAsync({
          address: quote.token_address as `0x${string}`,
          abi: erc20Abi,
          functionName: 'transfer',
          args: [
            quote.receive_address as `0x${string}`,
            BigInt(quote.amount_raw),
          ],
          chainId: quote.chain_id,
        })
      }

      setStatus('verifying')
      await pollVerify(txHash)
      onConfirmed(txHash)
    } catch (e: unknown) {
      // viem errors often expose a `.shortMessage`
      const err = e as { shortMessage?: string; message?: string }
      const msg = err.shortMessage || err.message || String(e)
      setError(msg)
      setStatus('error')
    }
  }

  const buttonLabel = (() => {
    switch (status) {
      case 'idle': return 'Pay now'
      case 'switching': return 'Switching chain…'
      case 'signing': return 'Confirm in wallet…'
      case 'verifying': return 'Verifying on-chain…'
      case 'error': return 'Retry'
    }
  })()

  const disabled = status !== 'idle' && status !== 'error'

  return (
    <div className="wc-root">
      <h3 style={{ marginTop: 0 }}>Pay {formatAmount(quote)}</h3>
      <p className="wc-small">
        Chain: <strong>{quote.chain_id}</strong><br />
        Recipient: <code>{quote.receive_address}</code>
      </p>
      <button className="wc-button" onClick={handlePay} disabled={disabled}>
        {buttonLabel}
      </button>
      {error && <div className="wc-error">{error}</div>}
    </div>
  )
}
