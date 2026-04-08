from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Order(models.Model):

    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('paid',        'Paid'),
        ('processing',  'Processing'),
        ('shipped',     'Shipped'),
        ('delivered',   'Delivered'),
        ('cancelled',   'Cancelled'),
    ]

    # Order Identification
    order_number = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    # Customer (nullable so guest checkout works)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    email      = models.EmailField()
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20)

    # Shipping Address (denormalized — snapshot at order time)
    address_line1  = models.CharField(max_length=255)
    address_line2  = models.CharField(max_length=255, blank=True)
    city           = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code    = models.CharField(max_length=20)
    country        = models.CharField(max_length=100, default='Nepal')

    notes = models.TextField(blank=True, help_text="Customer notes or special instructions")

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Pricing snapshot (NPR)
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax             = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost   = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total           = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])

    # Payment
    is_paid        = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_id     = models.CharField(max_length=200, blank=True)

    # Timestamps
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at   = models.DateTimeField(auto_now=True)
    paid_at      = models.DateTimeField(null=True, blank=True)
    shipped_at   = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)   # ← ADDED

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['is_paid', 'status']),
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.append(f"{self.city}, {self.state_province} {self.postal_code}")
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)

    @property
    def can_be_cancelled(self):
        return self.status in ('pending', 'paid', 'processing')


class OrderItem(models.Model):
    """
    Order line item — fully denormalized snapshot so historical orders
    are never affected by product edits or deletions.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # ── Product snapshot ───────────────────────────────────────────────
    # Keep product_id as integer (not FK) so the record survives product deletion
    product_id   = models.PositiveIntegerField()
    product_name = models.CharField(max_length=200)
    product_slug = models.SlugField(max_length=200)
    product_sku  = models.CharField(max_length=100, blank=True)   # ← ADDED

    # ── Variant snapshot (null = no variant selected) ──────────────────
    variant_id   = models.PositiveIntegerField(null=True, blank=True)   # ← ADDED
    variant_name = models.CharField(max_length=200, blank=True)         # ← ADDED
    variant_sku  = models.CharField(max_length=100, blank=True)         # ← ADDED

    # ── Pricing snapshot ───────────────────────────────────────────────
    price             = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    original_price    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # ← ADDED (compare_at_price snapshot)
    quantity          = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['id']

    def __str__(self):
        if self.variant_name:
            return f"{self.quantity}x {self.product_name} ({self.variant_name})"
        return f"{self.quantity}x {self.product_name}"

    @property
    def total_price(self):
        return self.price * self.quantity

    @property
    def was_on_sale(self):
        return bool(self.original_price and self.original_price > self.price)

    @property
    def savings(self):
        if self.was_on_sale:
            return (self.original_price - self.price) * self.quantity
        return Decimal('0.00')