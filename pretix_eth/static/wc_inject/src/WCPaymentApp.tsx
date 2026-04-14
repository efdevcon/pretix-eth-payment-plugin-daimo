import { useEffect, useState } from 'react'
import { useAccount } from 'wagmi'
import type { WCConfig } from './config'
import { ConnectStep } from './components/ConnectStep'
import { CheckoutStep } from './components/CheckoutStep'
import { SuccessStep } from './components/SuccessStep'
import { usePaymentOptions } from './hooks/usePaymentOptions'

type Stage = 'connect' | 'checkout' | 'success'

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
  const opts = usePaymentOptions(config)

  useEffect(() => {
    if (account.isConnected && stage === 'connect') setStage('checkout')
    if (!account.isConnected && stage !== 'connect') setStage('connect')
  }, [account.isConnected, stage])

  if (stage === 'connect') return <ConnectStep />

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
