import { useEffect, useState } from 'react'
import { useAccount } from 'wagmi'
import type { WCConfig } from './config'
import { ConnectStep } from './components/ConnectStep'
import { PreCheckoutStep } from './components/PreCheckoutStep'
import { CheckoutStep } from './components/CheckoutStep'
import { SuccessStep } from './components/SuccessStep'
import { usePaymentOptions } from './hooks/usePaymentOptions'

type Stage = 'connect' | 'pre-checkout' | 'checkout' | 'success'

export interface Quote {
  quote_id: string
  chain_id: number
  symbol: string
  token_address: string | null
  amount_raw: string
  receive_address: string
  intended_payer: string
  expires_at: number
  eth_price_usd: number | null
  order_total_usd: string
}

export function WCPaymentApp({ config }: { config: WCConfig }) {
  const account = useAccount()
  const [stage, setStage] = useState<Stage>('connect')
  const [txHash, setTxHash] = useState<string | null>(null)
  const [quote, setQuote] = useState<Quote | null>(null)

  // If orderCode is empty, we're on the initial checkout (order not yet created).
  // Full payment flow only works when order exists (retry/pay page).
  const hasOrder = Boolean(config.orderCode)

  const opts = usePaymentOptions(config, hasOrder)

  useEffect(() => {
    if (account.isConnected && stage === 'connect') {
      setStage(hasOrder ? 'checkout' : 'pre-checkout')
    }
    if (!account.isConnected && stage !== 'connect') setStage('connect')
  }, [account.isConnected, stage, hasOrder])

  if (stage === 'connect') return <ConnectStep hasOrder={hasOrder} />

  // Initial checkout — order doesn't exist yet. Show wallet info + "click Pay now"
  if (stage === 'pre-checkout') {
    return <PreCheckoutStep />
  }

  if (stage === 'checkout') {
    if (opts.isLoading) return <div className="wc-root wc-small">Loading payment options...</div>
    if (opts.isError || !opts.data) return <div className="wc-root wc-error">Failed to load payment options.</div>
    return (
      <CheckoutStep
        config={config}
        options={opts.data.options}
        ethAvailable={opts.data.eth_available}
        ethDisabledReason={opts.data.eth_disabled_reason}
        chainMetadata={opts.data.chain_metadata}
        onConfirmed={(hash, q) => { setTxHash(hash); setQuote(q); setStage('success') }}
      />
    )
  }

  if (stage === 'success' && quote && txHash) {
    return <SuccessStep quote={quote} txHash={txHash} />
  }

  return null
}
