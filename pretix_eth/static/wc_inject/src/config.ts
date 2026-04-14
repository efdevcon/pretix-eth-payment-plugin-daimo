// AppKit + wagmi setup. Reads config from a <script id="wc-config"> JSON tag
// injected by the Pretix checkout template.
import { createAppKit } from '@reown/appkit'
import { WagmiAdapter } from '@reown/appkit-adapter-wagmi'
import { mainnet, optimism, polygon, base, arbitrum } from '@reown/appkit/networks'
import type { AppKitNetwork } from '@reown/appkit/networks'

export interface WCConfig {
  wcProjectId: string
  orderCode: string
  orderSecret: string
  urlPrefix: string
  csrfToken: string
}

export function readConfig(): WCConfig {
  const el = document.getElementById('wc-config')
  if (!el) throw new Error('wc-config script tag missing from template')
  return JSON.parse(el.textContent || '{}') as WCConfig
}

const NETWORKS: [AppKitNetwork, ...AppKitNetwork[]] = [
  mainnet, optimism, polygon, base, arbitrum,
]

export function initAppKit(projectId: string) {
  const wagmiAdapter = new WagmiAdapter({
    projectId,
    networks: NETWORKS,
  })

  const appKit = createAppKit({
    adapters: [wagmiAdapter],
    networks: NETWORKS,
    projectId,
    metadata: {
      name: 'Pretix crypto payment',
      description: 'Pay for your ticket with crypto',
      url: typeof window !== 'undefined' ? window.location.origin : '',
      icons: [],
    },
    features: {
      analytics: false,
      email: false,
      socials: [],
    },
  })

  return { wagmiAdapter, appKit }
}
