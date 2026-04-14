import { useState } from 'react'
import { useAccount, useSignMessage } from 'wagmi'
import type { WCConfig } from '../config'
import type { PaymentOption } from '../hooks/usePaymentOptions'
import type { Quote } from '../WCPaymentApp'

const REASON_TEXT: Record<string, string> = {
  oracle_unavailable_or_diverged:
    'ETH payments temporarily unavailable. Our price oracles (Coinbase, Binance) disagree by more than 5% or are unreachable. Please pay with USDC or USDT0 instead.',
  oracle_error:
    'ETH payments temporarily unavailable due to a price lookup error. Please pay with USDC or USDT0 instead.',
}

function parseOrgAndEvent(): { organizer: string; event: string } {
  const match = window.location.pathname.match(/^\/([^/]+)\/([^/]+)/)
  if (!match) throw new Error('Could not parse organizer/event from URL')
  return { organizer: match[1], event: match[2] }
}

export function PickPaymentStep({
  config,
  options,
  ethAvailable,
  ethDisabledReason,
  chainMetadata,
  onQuoted,
}: {
  config: WCConfig
  options: PaymentOption[]
  ethAvailable: boolean
  ethDisabledReason: string | null
  chainMetadata: Record<string, { name: string; explorer_url: string }>
  onQuoted: (q: Quote) => void
}) {
  const [picked, setPicked] = useState<PaymentOption | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { address } = useAccount()
  const { signMessageAsync } = useSignMessage()

  async function handleContinue() {
    if (!picked || !address) return
    setError(null)
    setLoading(true)
    const { organizer, event } = parseOrgAndEvent()
    try {
      // 1. Fetch challenge
      const cr = await fetch(`${config.urlPrefix}/challenge/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          order_code: config.orderCode,
          order_secret: config.orderSecret,
          organizer,
          event,
        }),
      })
      if (!cr.ok) {
        const body = await cr.json().catch(() => ({}))
        throw new Error(body.error || `challenge HTTP ${cr.status}`)
      }
      const { nonce, message } = await cr.json()

      // 2. Sign the challenge message (no gas)
      const signature = await signMessageAsync({ message })

      // 3. Create the quote
      const qr = await fetch(`${config.urlPrefix}/create-quote/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          order_code: config.orderCode,
          order_secret: config.orderSecret,
          organizer,
          event,
          chain_id: picked.chain_id,
          symbol: picked.symbol,
          nonce,
          signature,
        }),
      })
      if (!qr.ok) {
        const body = await qr.json().catch(() => ({}))
        throw new Error(body.error || `create-quote HTTP ${qr.status}`)
      }
      const quote: Quote = await qr.json()
      onQuoted(quote)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="wc-root">
      <h3 style={{ marginTop: 0 }}>Select payment method</h3>

      {!ethAvailable && ethDisabledReason && (
        <div className="wc-notice">
          {REASON_TEXT[ethDisabledReason] || 'ETH payments temporarily unavailable.'}
        </div>
      )}

      {options.length === 0 && (
        <div className="wc-error">No payment options available.</div>
      )}

      {options.map((o) => {
        const key = `${o.chain_id}-${o.symbol}`
        const isPicked = picked?.chain_id === o.chain_id && picked?.symbol === o.symbol
        return (
          <div
            key={key}
            className={`wc-option ${isPicked ? 'selected' : ''}`}
            onClick={() => setPicked(o)}
          >
            <strong>{o.symbol}</strong>
            <span>on {o.chain_name}</span>
          </div>
        )
      })}

      <button
        className="wc-button"
        disabled={!picked || loading}
        onClick={handleContinue}
      >
        {loading ? 'Signing challenge\u2026' : 'Continue'}
      </button>

      {error && <div className="wc-error">{error}</div>}
    </div>
  )
}
