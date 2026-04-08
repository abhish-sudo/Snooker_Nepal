from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # ── Checkout & Payment Selection ──────────────────────────
    path('checkout/', views.checkout, name='checkout'),
    path('payment/<uuid:order_number>/', views.payment_selection, name='payment_selection'),

    # ── Universal Result Pages ─────────────────────────────────
    path('success/<uuid:order_number>/', views.success_page, name='success_page'),
    path('failure/<uuid:order_number>/', views.failure_page, name='failure_page_with_order'),
    path('failure/', views.failure_page, name='failure_page_no_order'),

    # ── Backwards Compatibility ────────────────────────────────
    path('confirmation/<uuid:order_number>/', views.order_confirmation, name='confirmation'),

    # ── eSewa ──────────────────────────────────────────────────
    path('esewa/<uuid:order_number>/', views.esewa_checkout, name='esewa_checkout'),
    path('esewa/success/', views.esewa_success, name='success'),        # eSewa callback URL
    path('esewa/failure/', views.esewa_failure, name='failure'),        # eSewa callback URL

    # ── Stripe ─────────────────────────────────────────────────
    # path('stripe/pay/<uuid:order_number>/', views.stripe_payment_page, name='stripe_payment_page'),
    path('stripe/<uuid:order_number>/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/success/', views.stripe_success, name='stripe_success'),
    path('stripe/cancel/<uuid:order_number>/', views.stripe_cancel, name='stripe_cancel'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),

    # ── Order Management ───────────────────────────────────────
    path('my-orders/', views.order_list, name='list'),
    path('cancel/<uuid:order_number>/', views.cancel_order, name='cancel_order'),
    path('<uuid:order_number>/', views.order_detail, name='detail'),    # keep last (catch-all uuid)
]