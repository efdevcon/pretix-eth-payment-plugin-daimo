import { useAppKit } from '@reown/appkit/react'

export function ConnectStep() {
  const { open } = useAppKit()
  return (
    <div className="wc-root">
      <h3 style={{ marginTop: 0 }}>Pay with crypto</h3>
      <p>Connect your wallet to continue. Supports MetaMask, Rainbow, Coinbase Wallet, WalletConnect, and more.</p>
      <button className="wc-button" onClick={() => open()}>
        Connect wallet
      </button>
    </div>
  )
}
