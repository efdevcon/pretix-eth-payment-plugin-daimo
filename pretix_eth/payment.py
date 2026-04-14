"""Pretix payment provider for WalletConnect-based crypto checkout."""
import logging
from collections import OrderedDict

from django import forms
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _
from pretix.base.payment import BasePaymentProvider

from pretix_eth.chains import SUPPORTED_CHAINS, ALL_SYMBOLS, CHAIN_METADATA

log = logging.getLogger(__name__)


class WalletConnectPayment(BasePaymentProvider):
    identifier = 'walletconnect'
    verbose_name = _('Pay with crypto (WalletConnect)')
    public_name = _('Crypto (USDC, USDT0, ETH)')
    abort_pending_allowed = True

    @property
    def settings_form_fields(self):
        base = OrderedDict(list(super().settings_form_fields.items()))
        base['receive_address'] = forms.CharField(
            label=_('Receive wallet address (EIP-55)'),
            max_length=42, min_length=42, required=True,
        )
        base['wc_project_id'] = forms.CharField(
            label=_('WalletConnect project ID (from cloud.reown.com)'),
            required=True,
        )
        base['alchemy_api_key'] = forms.CharField(
            label=_('Alchemy API key (optional; overridden by WC_ALCHEMY_API_KEY env)'),
            required=False,
            widget=forms.PasswordInput(render_value=True),
        )
        # Individual boolean per chain (hierarkey stores bools cleanly)
        for cid in SUPPORTED_CHAINS:
            base[f'chain_{cid}'] = forms.BooleanField(
                label=_('Chain: %s') % CHAIN_METADATA[cid]['name'],
                required=False, initial=True,
            )
        for sym in ALL_SYMBOLS:
            base[f'token_{sym}'] = forms.BooleanField(
                label=_('Token: %s') % sym,
                required=False, initial=True,
            )
        base['quote_ttl_seconds'] = forms.IntegerField(
            label=_('Quote TTL (seconds)'),
            initial=600, min_value=60, max_value=3600,
        )
        base['min_confirmations'] = forms.IntegerField(
            label=_('Minimum confirmations'),
            initial=1, min_value=0, max_value=50,
        )
        return base

    def is_allowed(self, request=None, total=None):
        return bool(self.settings.get('receive_address')) and bool(self.settings.get('wc_project_id'))

    def checkout_prepare(self, request: HttpRequest, cart):
        return True

    def payment_form_render(self, request: HttpRequest) -> str:
        return ''

    def checkout_confirm_render(self, request: HttpRequest, order=None, info_data=None) -> str:
        if order:
            # Payment retry/continue — order exists, show full crypto checkout UI
            tpl = get_template('pretix_eth/checkout_payment_confirm.html')
            ctx = {
                'wc_project_id': self.settings.get('wc_project_id'),
                'url_prefix': '/plugin/wc',
                'order_code': order.code,
                'order_secret': order.secret,
            }
            return tpl.render(ctx, request=request)
        else:
            # Initial checkout — order not yet created, just confirm payment method
            return (
                '<div class="wc-root">'
                '<p>You will pay with crypto (USDC, USDT0, or ETH) after confirming your order.</p>'
                '</div>'
            )

    def payment_is_valid_session(self, request: HttpRequest) -> bool:
        return True

    def execute_payment(self, request: HttpRequest, payment):
        # Redirect directly to the payment confirm page where our React UI loads.
        # This skips the default Pretix flow (thanks page → pay/change → pay/confirm).
        order = payment.order
        org = order.event.organizer.slug
        evt = order.event.slug
        return f'/{org}/{evt}/order/{order.code}/{order.secret}/pay/{payment.local_id}/confirm'

    def payment_pending_render(self, request: HttpRequest, payment) -> str:
        tpl = get_template('pretix_eth/pending.html')
        info = payment.info_data or {}
        tx = info.get('tx_hash')
        chain_id = info.get('chain_id')
        explorer = CHAIN_METADATA.get(chain_id, {}).get('explorer_url', '')
        return tpl.render({
            'tx_hash': tx,
            'explorer_url': f'{explorer}{tx}' if tx else None,
        })

    def payment_control_render(self, request: HttpRequest, payment) -> str:
        tpl = get_template('pretix_eth/control.html')
        info = payment.info_data or {}
        chain_id = info.get('chain_id')
        explorer = CHAIN_METADATA.get(chain_id, {}).get('explorer_url', '')
        return tpl.render({
            'tx_hash': info.get('tx_hash'),
            'chain_id': chain_id,
            'chain_name': CHAIN_METADATA.get(chain_id, {}).get('name'),
            'token_symbol': info.get('token_symbol'),
            'payer': info.get('payer'),
            'amount': info.get('amount'),
            'block_number': info.get('block_number'),
            'explorer_url': f'{explorer}{info.get("tx_hash", "")}' if info.get('tx_hash') else None,
        })

    def matching_id(self, payment):
        return (payment.info_data or {}).get('tx_hash')

    def payment_refund_supported(self, payment):
        return False

    def payment_partial_refund_supported(self, payment):
        return False
