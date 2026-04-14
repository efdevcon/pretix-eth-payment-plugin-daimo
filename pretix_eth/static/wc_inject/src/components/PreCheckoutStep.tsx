import { useAccount } from 'wagmi'
import { WalletHeader } from './WalletHeader'

export function PreCheckoutStep() {
  const { address } = useAccount()

  return (
    <div className="wc-root">
      <WalletHeader />
      <h3 style={{ marginTop: 0 }}>Pay with crypto</h3>
      <p>
        Wallet connected: <code>{address?.slice(0, 6)}...{address?.slice(-4)}</code>
      </p>
      <p className="wc-small">
        Click <strong>"Pay now"</strong> below to create your order. You will then select your chain and token and confirm the payment in your wallet.
      </p>
    </div>
  )
}
