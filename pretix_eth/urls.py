"""URL routes for the WalletConnect payment plugin.

Pretix auto-discovers this file and mounts urlpatterns globally
(see pretix.multidomain.maindomain_urlconf).
"""
from django.urls import path

from pretix_eth import views

urlpatterns = [
    path('plugin/wc/payment-options/', views.payment_options, name='wc_payment_options'),
    path('plugin/wc/challenge/', views.challenge, name='wc_challenge'),
    path('plugin/wc/create-quote/', views.create_quote, name='wc_create_quote'),
    path('plugin/wc/verify/', views.verify, name='wc_verify'),
]
