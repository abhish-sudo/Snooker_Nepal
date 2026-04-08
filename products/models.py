from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
 
User = get_user_model()
 
 
# ──────────────────────────────────────────────
#  BRAND
# ──────────────────────────────────────────────
 
class Brand(models.Model):
    """
    Equipment brands like Riley, Predator, Powerglide, BCE, etc.
    Allows filtering/browsing by brand on the frontend.
    """
    name        = models.CharField(max_length=200, unique=True)
    slug        = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo        = models.ImageField(upload_to='brands/logos/', blank=True, null=True)
    website     = models.URLField(blank=True)
    is_active   = models.BooleanField(default=True)
 
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['name']
 
    def __str__(self):
        return self.name
 
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
 
 
# ──────────────────────────────────────────────
#  CATEGORY
# ──────────────────────────────────────────────
 
class Category(models.Model):
    """
    Hierarchical categories:
      e.g.  Cues > Break Cues
            Cues > Snooker Cues
            Accessories > Chalk
            Accessories > Tips
            Balls > Full Sets
    """
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='categories/', blank=True, null=True)
 
    # Self-referential FK for parent/child hierarchy
    parent      = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='subcategories'
    )
 
    is_active   = models.BooleanField(default=True)
    order       = models.PositiveIntegerField(default=0, help_text="Display order in menus")
 
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
 
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
 
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
 
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
 
    def get_absolute_url(self):
        return reverse('products:category', args=[self.slug])
 
 
# ──────────────────────────────────────────────
#  TAG
# ──────────────────────────────────────────────
 
class Tag(models.Model):
    """
    Flexible tagging for products.
    e.g.  'professional', 'beginner', 'tournament-grade', 'handmade'
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
 
    def __str__(self):
        return self.name
 
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
 
 
# ──────────────────────────────────────────────
#  PRODUCT
# ──────────────────────────────────────────────
 
class Product(models.Model):
    """
    Core product model for Snooker Nepal accessories store.
 
    Design decisions:
    - Soft delete (is_active) preserves historical order records
    - Decimal prices for financial accuracy (NPR)
    - Slug-based URLs for SEO
    - ProductVariant model handles size/weight variations (e.g. cue tip sizes)
    - ProductImage model supports rotating image gallery
    - Brand + Category + Tags for rich filtering
    """
 
    # ── Relationships ──────────────────────────
    category    = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products'
    )
    brand       = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products'
    )
    tags        = models.ManyToManyField(Tag, blank=True, related_name='products')
 
    # ── Basic Info ─────────────────────────────
    name              = models.CharField(max_length=200, db_index=True)
    slug              = models.SlugField(max_length=200, unique=True, blank=True)
    sku               = models.CharField(
        max_length=100, unique=True, blank=True,
        help_text="Stock Keeping Unit — auto-generated if left blank"
    )
    short_description = models.CharField(max_length=300, blank=True)
    description       = models.TextField()
 
    # ── Snooker-Specific Specs ─────────────────
    # These cover cues, tips, chalk, cases, balls, etc.
    weight_grams      = models.DecimalField(
        max_digits=7, decimal_places=2,
        blank=True, null=True,
        help_text="Product weight in grams (important for cues & balls)"
    )
    length_cm         = models.DecimalField(
        max_digits=6, decimal_places=2,
        blank=True, null=True,
        help_text="Length in cm (for cues and cue cases)"
    )
    material          = models.CharField(
        max_length=200, blank=True,
        help_text="e.g. Ash, Maple, Leather, Fibre"
    )
    tip_size_mm       = models.DecimalField(
        max_digits=4, decimal_places=1,
        blank=True, null=True,
        help_text="Tip diameter in mm (for cues and tips)"
    )
    joint_type        = models.CharField(
        max_length=100, blank=True,
        help_text="e.g. 3/8x10, Radial, Uni-loc (for cues)"
    )
    color             = models.CharField(max_length=100, blank=True)
    country_of_origin = models.CharField(max_length=100, blank=True)
 
    # ── Pricing (NPR) ──────────────────────────
    price             = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Selling price in NPR"
    )
    compare_at_price  = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Original/MRP price — shown as strikethrough when higher than price"
    )
    cost_price        = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Your purchase/cost price — not shown to customers"
    )
 
    # ── Inventory ──────────────────────────────
    stock_quantity    = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="Show 'Low Stock' warning when quantity falls below this"
    )
    allow_backorder   = models.BooleanField(
        default=False,
        help_text="Allow purchase even when out of stock"
    )
 
    # ── Shipping ───────────────────────────────
    shipping_weight_kg = models.DecimalField(
        max_digits=6, decimal_places=3,
        blank=True, null=True,
        help_text="Shipping weight in kg for delivery calculation"
    )
    is_fragile        = models.BooleanField(
        default=False,
        help_text="Flag for special packaging requirements"
    )
    free_shipping     = models.BooleanField(default=False)
 
    # ── Product Status Flags ───────────────────
    is_active         = models.BooleanField(default=True, db_index=True)
    is_featured       = models.BooleanField(default=False, db_index=True)
    is_bestseller     = models.BooleanField(default=False)
    is_new_arrival    = models.BooleanField(default=False)
    is_limited_edition = models.BooleanField(default=False)
 
    # ── SEO ────────────────────────────────────
    meta_title        = models.CharField(max_length=200, blank=True)
    meta_description  = models.CharField(max_length=300, blank=True)
 
    # ── Metadata ───────────────────────────────
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['is_active', 'is_bestseller']),
            models.Index(fields=['-created_at']),
        ]
 
    def __str__(self):
        return self.name
 
    # ── Save logic ─────────────────────────────
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
 
        if not self.short_description and self.description:
            self.short_description = self.description[:297] + '...'
 
        # Auto-generate SKU: e.g. SNK-00042
        if not self.sku:
            super().save(*args, **kwargs)
            self.sku = f"SNK-{self.pk:05d}"
 
        super().save(*args, **kwargs)
 
    # ── URLs ───────────────────────────────────
    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])
 
    # ── Computed properties ────────────────────
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 or self.allow_backorder
 
    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold
 
    @property
    def is_on_sale(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)
 
    @property
    def discount_percentage(self):
        if self.is_on_sale:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return int(discount)
        return 0
 
    @property
    def profit_margin(self):
        """Internal use only — not exposed to templates"""
        if self.cost_price and self.price:
            return self.price - self.cost_price
        return None
 
    # ── Image helpers ──────────────────────────
    def get_main_image(self):
        """Returns primary image, falls back to first image"""
        return (
            self.images.filter(is_primary=True).first()
            or self.images.first()
        )
 
    def get_all_images(self):
        """Returns all images ordered for gallery/carousel"""
        return self.images.all().order_by('order', 'created_at')
 
    # ── Review helpers ─────────────────────────
    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None
 
    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()
 
 
# ──────────────────────────────────────────────
#  PRODUCT VARIANT
# ──────────────────────────────────────────────
 
class ProductVariant(models.Model):
    """
    Variants for products that come in multiple options.
    Examples:
      - Cue tips: 9mm, 9.5mm, 10mm
      - Cue cases: 1-piece, 2-piece, 3/4
      - Chalk: Blue Diamond, Taom, Predator
    Each variant can override price and stock independently.
    """
    product        = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name           = models.CharField(
        max_length=200,
        help_text="e.g. '9.5mm', '3/4 Case', 'Blue Diamond'"
    )
    sku            = models.CharField(max_length=100, unique=True, blank=True)
    price_override = models.DecimalField(
        max_digits=10, decimal_places=2,
        blank=True, null=True,
        help_text="Leave blank to use the main product price"
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active      = models.BooleanField(default=True)
    order          = models.PositiveIntegerField(default=0)
 
    class Meta:
        ordering = ['order', 'name']
 
    def __str__(self):
        return f"{self.product.name} — {self.name}"
 
    @property
    def effective_price(self):
        return self.price_override if self.price_override else self.product.price
 
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
 
 
# ──────────────────────────────────────────────
#  PRODUCT IMAGE
# ──────────────────────────────────────────────
 
class ProductImage(models.Model):
    """
    Multiple images per product for rotating gallery / carousel.
 
    Usage on frontend:
      - product.get_all_images  →  feed into a JS carousel (Swiper, Slick, etc.)
      - is_primary=True image   →  shown in product listing cards
      - order field             →  controls carousel sequence
      - image_type              →  lets you separate main shots from detail/lifestyle shots
    """
 
    IMAGE_TYPE_CHOICES = [
        ('main',      'Main Shot'),
        ('gallery',   'Gallery'),
        ('detail',    'Close-up / Detail'),
        ('lifestyle', 'Lifestyle'),
        ('size_chart','Size Chart'),
    ]
 
    product    = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    variant    = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='images',
        help_text="Link image to a specific variant (optional)"
    )
    image      = models.ImageField(upload_to='products/%Y/%m/')
    alt_text   = models.CharField(
        max_length=200, blank=True,
        help_text="Descriptive alt text for accessibility and SEO"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="This image appears on listing cards and as the first carousel slide"
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPE_CHOICES,
        default='gallery'
    )
    order      = models.PositiveIntegerField(
        default=0,
        help_text="Lower number = appears first in carousel"
    )
 
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
            models.Index(fields=['product', 'order']),
        ]
 
    def __str__(self):
        return f"{self.product.name} — {self.get_image_type_display()} (#{self.order})"
 
    def save(self, *args, **kwargs):
        # Only one primary image allowed per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
 
 
# ──────────────────────────────────────────────
#  PRODUCT REVIEW
# ──────────────────────────────────────────────
 
class ProductReview(models.Model):
    """
    Verified customer reviews with star ratings.
    Only approved reviews are shown publicly.
    average_rating and review_count are computed on Product via properties.
    """
    product     = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user        = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating      = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 to 5 stars"
    )
    title       = models.CharField(max_length=200, blank=True)
    body        = models.TextField()
    is_approved = models.BooleanField(
        default=False,
        help_text="Only approved reviews are visible to customers"
    )
    is_verified_purchase = models.BooleanField(
        default=False,
        help_text="Auto-set to True if the user has an order containing this product"
    )
 
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ['-created_at']
        # One review per user per product
        unique_together = ('product', 'user')
 
    def __str__(self):
        return f"{self.user} — {self.product.name} ({self.rating}★)"
 
 
# ──────────────────────────────────────────────
#  RELATED PRODUCTS
# ──────────────────────────────────────────────
 
class RelatedProduct(models.Model):
    """
    Manually curated 'You may also like' / 'Frequently bought together' links.
    e.g.  Cue  →  Tip, Chalk, Cue Case
    """
    RELATION_CHOICES = [
        ('similar',    'Similar Product'),
        ('bundle',     'Frequently Bought Together'),
        ('accessory',  'Recommended Accessory'),
        ('upgrade',    'Upgrade Option'),
    ]
 
    from_product    = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_from'
    )
    to_product      = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='related_to'
    )
    relation_type   = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        default='similar'
    )
    order           = models.PositiveIntegerField(default=0)
 
    class Meta:
        ordering = ['order']
        unique_together = ('from_product', 'to_product')
 
    def __str__(self):
        return f"{self.from_product.name} → {self.to_product.name} ({self.relation_type})"