import { useAccount, useDisconnect } from 'wagmi'

export function WalletHeader() {
  const { address } = useAccount()
  const { disconnect } = useDisconnect()

  if (!address) return null

  const short = `${address.slice(0, 6)}...${address.slice(-4)}`

  return (
    <div className="wc-wallet-header">
      <span className="wc-small">
        Connected: <code>{short}</code>
      </span>
      <button
        className="wc-link-button"
        onClick={() => disconnect()}
      >
        Disconnect
      </button>
    </div>
  )
}
