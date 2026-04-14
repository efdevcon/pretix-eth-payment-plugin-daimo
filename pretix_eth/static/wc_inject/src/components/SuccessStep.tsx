import { useEffect } from 'react'
import type { Quote } from '../WCPaymentApp'

export function SuccessStep({ quote: _quote, txHash }: { quote: Quote; txHash: string }) {
  useEffect(() => {
    const t = setTimeout(() => { window.location.reload() }, 2000)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="wc-root">
      <h3 style={{ marginTop: 0, color: '#2e7d32' }}>Payment confirmed</h3>
      <p className="wc-small">
        Transaction: <code style={{ wordBreak: 'break-all' }}>{txHash}</code>
      </p>
      <p>Finalizing your order…</p>
    </div>
  )
}
