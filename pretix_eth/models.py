from django.db import models
from django.utils import timezone

from pretix.base.models import OrderPayment


class SignedMessage(models.Model):

    signature = models.CharField(max_length=132)
    raw_message = models.TextField()
    sender_address = models.CharField(max_length=42)
    recipient_address = models.CharField(max_length=42)
    chain_id = models.IntegerField()
    order_payment = models.ForeignKey(
        to=OrderPayment,
        on_delete=models.CASCADE,
        related_name='signed_messages',
    )
    transaction_hash = models.CharField(max_length=66, null=True, unique=True)
    safe_app_transaction_url = models.TextField(null=True, unique=True)
    invalid = models.BooleanField(default=False)
    created_at = models.DateTimeField(editable=False, null=True)
    is_confirmed = models.BooleanField(
        default=False)  # true for the payment that arrived

    def save(self, *args, **kwargs):
        if self.pk is None or self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def invalidate(self):
        if not self.invalid:
            self.invalid = True
            self.save()

    @property
    def age(self):
        return timezone.now().timestamp() - self.created_at.timestamp()

    @property
    def another_signature_submitted(self):
        if self.order_payment is None:
            return False

        return SignedMessage.objects.filter(
            order_payment__order=self.order_payment.order,
            invalid=False
        ).exists()


class WCPaymentAttempt(models.Model):
    """Tracks crypto payment attempts for the WalletConnect flow.
    Enforces one-time use of tx_hash to prevent cross-order replay."""
    STATE_CLAIMING = 'claiming'
    STATE_COMPLETED = 'completed'
    STATE_CHOICES = [
        (STATE_CLAIMING, 'claiming'),
        (STATE_COMPLETED, 'completed'),
    ]

    tx_hash = models.CharField(max_length=66, unique=True, db_index=True)
    quote_id = models.CharField(max_length=32, db_index=True)
    order_code = models.CharField(max_length=16)
    payer = models.CharField(max_length=42)
    chain_id = models.IntegerField()
    state = models.CharField(max_length=16, choices=STATE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'pretix_eth'
