import { appKitInstance } from '../config'

export function ConnectStep() {
  return (
    <div className="wc-root">
      <h3 style={{ marginTop: 0 }}>Pay with crypto</h3>
      <p>Connect your wallet to continue. Supports MetaMask, Rainbow, Coinbase Wallet, WalletConnect, and more.</p>
      {/* AppKit's built-in web component — shows Connect button, then account info once connected */}
      <appkit-button />
      <div style={{ marginTop: 12 }}>
        <button className="wc-button" onClick={() => appKitInstance?.open()}>
          Connect wallet
        </button>
      </div>
    </div>
  )
}

// Declare the web component so TypeScript doesn't complain
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'appkit-button': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement>
    }
  }
}
