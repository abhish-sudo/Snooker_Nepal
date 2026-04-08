from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Brand, Category, Tag,
    Product, ProductVariant, ProductImage,
    ProductReview, RelatedProduct
)


# ──────────────────────────────────────────────
#  BRAND
# ──────────────────────────────────────────────

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


# ──────────────────────────────────────────────
#  CATEGORY
# ──────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'parent', 'slug', 'is_active', 'order')
    list_filter   = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')


# ──────────────────────────────────────────────
#  TAG
# ──────────────────────────────────────────────

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ──────────────────────────────────────────────
#  PRODUCT VARIANT (inline)
# ──────────────────────────────────────────────

class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ('name', 'sku', 'price_override', 'stock_quantity', 'is_active', 'order')


# ──────────────────────────────────────────────
#  PRODUCT IMAGE (inline)
# ──────────────────────────────────────────────

class ProductImageInline(admin.TabularInline):
    model       = ProductImage
    extra       = 1
    fields      = ('image', 'alt_text', 'image_type', 'is_primary', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px; border-radius:4px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'


# ──────────────────────────────────────────────
#  RELATED PRODUCT (inline)
# ──────────────────────────────────────────────

class RelatedProductInline(admin.TabularInline):
    model          = RelatedProduct
    fk_name        = 'from_product'
    extra          = 1
    fields         = ('to_product', 'relation_type', 'order')
    autocomplete_fields = ('to_product',)


# ──────────────────────────────────────────────
#  PRODUCT
# ──────────────────────────────────────────────

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'brand', 'category', 'price',
        'stock_quantity', 'is_active', 'is_featured',
        'is_bestseller', 'is_new_arrival', 'created_at'
    )
    list_filter = (
        'is_active', 'is_featured', 'is_bestseller',
        'is_new_arrival', 'is_limited_edition',
        'category', 'brand'
    )
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('tags',)
    readonly_fields   = ('sku', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    inlines = [ProductImageInline, ProductVariantInline, RelatedProductInline]

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'name', 'slug', 'sku',
                'category', 'brand', 'tags',
                'short_description', 'description',
            )
        }),
        ('Snooker Specifications', {
            'classes': ('collapse',),
            'fields': (
                'weight_grams', 'length_cm', 'tip_size_mm',
                'material', 'joint_type', 'color', 'country_of_origin',
            )
        }),
        ('Pricing (NPR)', {
            'fields': ('price', 'compare_at_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': (
                'stock_quantity', 'low_stock_threshold',
                'allow_backorder',
            )
        }),
        ('Shipping', {
            'classes': ('collapse',),
            'fields': ('shipping_weight_kg', 'is_fragile', 'free_shipping')
        }),
        ('Status Flags', {
            'fields': (
                'is_active', 'is_featured', 'is_bestseller',
                'is_new_arrival', 'is_limited_edition',
            )
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description')
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )


# ──────────────────────────────────────────────
#  PRODUCT REVIEW
# ──────────────────────────────────────────────

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display  = ('product', 'user', 'rating', 'is_approved', 'is_verified_purchase', 'created_at')
    list_filter   = ('is_approved', 'is_verified_purchase', 'rating')
    search_fields = ('product__name', 'user__username', 'body')
    actions       = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f'{queryset.count()} review(s) approved.')
    approve_reviews.short_description = 'Approve selected reviews'