from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, OrderItem


# ──────────────────────────────────────────────
#  ORDER ITEM INLINE
# ──────────────────────────────────────────────

class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    extra  = 0
    can_delete = False
    readonly_fields = [
        'product_name', 'product_sku',
        'variant_name', 'variant_sku',
        'price', 'original_price', 'quantity', 'line_total'
    ]
    fields = [
        'product_name', 'product_sku',
        'variant_name', 'price', 'original_price',
        'quantity', 'line_total'
    ]

    def line_total(self, obj):
        return format_html(
            '<strong>NPR {}</strong>',
            f'{obj.total_price:,.2f}'
        )
    line_total.short_description = 'Line Total'


# ──────────────────────────────────────────────
#  ORDER
# ──────────────────────────────────────────────

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number_short',
        'full_name',
        'email',
        'phone',
        'total_display',
        'status_badge',
        'payment_method',
        'is_paid',
        'created_at',
    ]
    list_filter  = ['status', 'is_paid', 'payment_method', 'created_at']
    search_fields = [
        'order_number', 'email',
        'first_name', 'last_name', 'phone'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at',
        'paid_at', 'shipped_at', 'delivered_at', 'cancelled_at',
        'subtotal', 'tax', 'shipping_cost', 'total', 'discount_amount',
        'full_name_display', 'full_address_display',
    ]
    inlines  = [OrderItemInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Order', {
            'fields': ('order_number', 'status', 'user')
        }),
        ('Customer', {
            'fields': (
                'first_name', 'last_name',
                'email', 'phone',
            )
        }),
        ('Shipping Address', {
            'fields': (
                'address_line1', 'address_line2',
                'city', 'state_province',
                'postal_code', 'country',
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Pricing (NPR)', {
            'fields': (
                'subtotal', 'discount_amount',
                'tax', 'shipping_cost', 'total',
            )
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_method', 'payment_id')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': (
                'created_at', 'updated_at',
                'paid_at', 'shipped_at',
                'delivered_at', 'cancelled_at',
            )
        }),
    )

    # ── List display helpers ──────────────────

    def order_number_short(self, obj):
        short = str(obj.order_number)[:8].upper()
        return format_html(
            '<span style="font-family: monospace; font-size: 12px;">{}</span>',
            short
        )
    order_number_short.short_description = 'Order #'

    def total_display(self, obj):
        return f'NPR {obj.total:,.2f}'
    total_display.short_description = 'Total'

    def status_badge(self, obj):
        colors = {
            'pending':    '#f39c12',
            'paid':       '#3498db',
            'processing': '#2980b9',
            'shipped':    '#9b59b6',
            'delivered':  '#27ae60',
            'cancelled':  '#e74c3c',
        }
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 10px;'
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            colors.get(obj.status, '#777'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def full_name_display(self, obj):
        return obj.full_name
    full_name_display.short_description = 'Full Name'

    def full_address_display(self, obj):
        return obj.full_address
    full_address_display.short_description = 'Full Address'

    # ── Bulk actions ─────────────────────────

    actions = [
        'mark_as_processing',
        'mark_as_shipped',
        'mark_as_delivered',
        'mark_as_cancelled',
    ]

    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} order(s) marked as Processing.')
    mark_as_processing.short_description = 'Mark selected → Processing'

    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped', shipped_at=timezone.now())
        self.message_user(request, f'{updated} order(s) marked as Shipped.')
    mark_as_shipped.short_description = 'Mark selected → Shipped'

    def mark_as_delivered(self, request, queryset):
        updated = queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} order(s) marked as Delivered.')
    mark_as_delivered.short_description = 'Mark selected → Delivered'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled', cancelled_at=timezone.now())
        self.message_user(request, f'{updated} order(s) Cancelled.')
    mark_as_cancelled.short_description = 'Mark selected → Cancelled'


# ──────────────────────────────────────────────
#  ORDER ITEM
# ──────────────────────────────────────────────

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = [
        'order_link', 'product_name', 'variant_name',
        'product_sku', 'quantity', 'price_display', 'total_display'
    ]
    list_filter   = ['order__status', 'order__created_at']
    search_fields = ['product_name', 'product_sku', 'order__email']
    readonly_fields = [
        'order', 'product_id', 'product_name', 'product_slug', 'product_sku',
        'variant_id', 'variant_name', 'variant_sku',
        'price', 'original_price', 'quantity',
    ]

    def order_link(self, obj):
        short = str(obj.order.order_number)[:8].upper()
        return format_html(
            '<a href="/admin/orders/order/{}/change/" style="font-family:monospace;">{}</a>',
            obj.order.pk, short
        )
    order_link.short_description = 'Order'

    def price_display(self, obj):
        return f'NPR {obj.price:,.2f}'
    price_display.short_description = 'Unit Price'

    def total_display(self, obj):
        return format_html('<strong>NPR {}</strong>', f'{obj.total_price:,.2f}')
    total_display.short_description = 'Line Total'