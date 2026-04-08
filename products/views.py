from django.views.generic import ListView, DetailView
from django.db.models import Q, Prefetch, Avg, Count
from django.shortcuts import get_object_or_404

from .models import (
    Product, Category, Brand,
    ProductImage, ProductVariant,
    ProductReview, RelatedProduct, Tag
)


# ──────────────────────────────────────────────
#  SHARED QUERY HELPER
# ──────────────────────────────────────────────

def base_product_queryset():
    """
    Reusable optimized queryset used across multiple views.
    Avoids N+1 queries by eager-loading related data.
    """
    return Product.objects.filter(
        is_active=True
    ).select_related(
        'category',
        'brand'
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.order_by('order', 'created_at')
        ),
        'tags',
        'variants',
    )


def primary_image_queryset():
    """Only fetch the primary/listing image — used on list/card views."""
    return Product.objects.filter(
        is_active=True
    ).select_related(
        'category',
        'brand'
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.filter(is_primary=True)
        )
    )


# ──────────────────────────────────────────────
#  HOME
# ──────────────────────────────────────────────

class HomeView(ListView):
    """
    Homepage — featured products, new arrivals, bestsellers, brand showcase.
    Each section uses a separate optimised query.
    """
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'featured_products'

    def get_queryset(self):
        return primary_image_queryset().filter(is_featured=True)[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['new_arrivals'] = primary_image_queryset().filter(
            is_new_arrival=True
        )[:4]

        context['bestsellers'] = primary_image_queryset().filter(
            is_bestseller=True
        )[:4]

        context['limited_edition'] = primary_image_queryset().filter(
            is_limited_edition=True
        )[:3]

        # Brand showcase (logos displayed on homepage)
        context['brands'] = Brand.objects.filter(is_active=True).order_by('name')

        # Top-level categories for navigation/hero tiles
        context['categories'] = Category.objects.filter(
            is_active=True,
            parent__isnull=True  # only root categories
        ).order_by('order', 'name')

        return context


# ──────────────────────────────────────────────
#  PRODUCT LIST
# ──────────────────────────────────────────────

class ProductListView(ListView):
    """
    Full product catalog with:
    - Text search (name, description)
    - Category filter
    - Brand filter
    - Tag filter
    - Price range filter
    - Sort options
    - Pagination
    """
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = primary_image_queryset()

        # ── Text search ────────────────────────
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(short_description__icontains=q) |
                Q(brand__name__icontains=q) |
                Q(tags__name__icontains=q)
            ).distinct()

        # ── Category filter ────────────────────
        category_slug = self.kwargs.get('category_slug') or self.request.GET.get('category')
        if category_slug:
            try:
                cat = Category.objects.get(slug=category_slug, is_active=True)
                # Include products from subcategories too
                subcategory_ids = list(cat.subcategories.values_list('id', flat=True))
                queryset = queryset.filter(
                    category__in=[cat.id] + subcategory_ids
                )
            except Category.DoesNotExist:
                pass

        # ── Brand filter ───────────────────────
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            queryset = queryset.filter(brand__slug=brand_slug)

        # ── Tag filter ─────────────────────────
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        # ── Price range filter ─────────────────
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # ── Stock filter ───────────────────────
        in_stock_only = self.request.GET.get('in_stock')
        if in_stock_only:
            queryset = queryset.filter(stock_quantity__gt=0)

        # ── Sort ───────────────────────────────
        sort_options = {
            'newest':       '-created_at',
            'price_asc':    'price',
            'price_desc':   '-price',
            'name_asc':     'name',
            'name_desc':    '-name',
        }
        sort = self.request.GET.get('sort', 'newest')
        queryset = queryset.order_by(sort_options.get(sort, '-created_at'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Sidebar filter data
        context['categories'] = Category.objects.filter(
            is_active=True,
            parent__isnull=True
        ).prefetch_related('subcategories').order_by('order', 'name')

        context['brands'] = Brand.objects.filter(is_active=True).order_by('name')
        context['tags']   = Tag.objects.all().order_by('name')

        # Pass active filters back to template for UI state
        context['search_query']    = self.request.GET.get('q', '')
        context['current_sort']    = self.request.GET.get('sort', 'newest')
        context['current_brand']   = self.request.GET.get('brand', '')
        context['current_tag']     = self.request.GET.get('tag', '')
        context['current_min']     = self.request.GET.get('min_price', '')
        context['current_max']     = self.request.GET.get('max_price', '')
        context['in_stock_only']   = self.request.GET.get('in_stock', '')

        # Current category (for breadcrumbs / heading)
        category_slug = self.kwargs.get('category_slug') or self.request.GET.get('category')
        if category_slug:
            context['current_category'] = Category.objects.filter(
                slug=category_slug
            ).first()

        return context


# ──────────────────────────────────────────────
#  PRODUCT DETAIL
# ──────────────────────────────────────────────

class ProductDetailView(DetailView):
    """
    Full product page with:
    - Rotating image gallery (all images ordered)
    - Product variants (tip sizes, case types, etc.)
    - Approved customer reviews + average rating
    - Related products (from RelatedProduct model)
    - Fallback: same-category suggestions
    """
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True
        ).select_related(
            'category',
            'brand'
        ).prefetch_related(
            # All images ordered for the carousel
            Prefetch(
                'images',
                queryset=ProductImage.objects.order_by('order', 'created_at')
            ),
            # Active variants (e.g. tip sizes)
            Prefetch(
                'variants',
                queryset=ProductVariant.objects.filter(
                    is_active=True
                ).order_by('order', 'name')
            ),
            # Approved reviews with user info
            Prefetch(
                'reviews',
                queryset=ProductReview.objects.filter(
                    is_approved=True
                ).select_related('user').order_by('-created_at'),
                to_attr='approved_reviews'
            ),
            'tags',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # ── Rotating gallery images ────────────
        context['gallery_images'] = product.images.all()

        # ── Variants ───────────────────────────
        context['variants'] = product.variants.filter(is_active=True)

        # ── Reviews ────────────────────────────
        context['reviews']        = product.approved_reviews
        context['review_count']   = len(product.approved_reviews)
        context['average_rating'] = product.average_rating

        # Rating breakdown (5★: N, 4★: N, ...)
        context['rating_breakdown'] = {
            star: sum(1 for r in product.approved_reviews if r.rating == star)
            for star in range(5, 0, -1)
        }

        # ── Related products ───────────────────
        # First try curated RelatedProduct links
        curated_related = RelatedProduct.objects.filter(
            from_product=product
        ).select_related(
            'to_product__category',
            'to_product__brand'
        ).prefetch_related(
            Prefetch(
                'to_product__images',
                queryset=ProductImage.objects.filter(is_primary=True)
            )
        ).order_by('order')[:6]

        if curated_related.exists():
            context['related_products'] = [rp.to_product for rp in curated_related]
            context['related_label']    = 'You May Also Like'
        else:
            # Fallback: other active products in same category
            context['related_products'] = primary_image_queryset().filter(
                category=product.category
            ).exclude(pk=product.pk)[:4]
            context['related_label'] = 'More from this Category'

        # ── Breadcrumb data ────────────────────
        context['breadcrumbs'] = self._build_breadcrumbs(product)

        return context

    def _build_breadcrumbs(self, product):
        crumbs = [{'name': 'Home', 'url': '/'}]
        if product.category:
            if product.category.parent:
                crumbs.append({
                    'name': product.category.parent.name,
                    'url':  product.category.parent.get_absolute_url()
                })
            crumbs.append({
                'name': product.category.name,
                'url':  product.category.get_absolute_url()
            })
        crumbs.append({'name': product.name, 'url': None})
        return crumbs


# ──────────────────────────────────────────────
#  CATEGORY
# ──────────────────────────────────────────────

class CategoryView(ListView):
    """
    Category page — shows products from this category AND its subcategories.
    e.g.  /category/cues/  shows all cues including break-cues, snooker-cues, etc.
    """
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_active=True
        )
        # Include subcategory products
        subcategory_ids = list(
            self.category.subcategories.values_list('id', flat=True)
        )
        return primary_image_queryset().filter(
            category__in=[self.category.id] + subcategory_ids
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category']       = self.category
        context['subcategories']  = self.category.subcategories.filter(is_active=True)
        context['product_count']  = self.get_queryset().count()

        # Breadcrumbs
        crumbs = [{'name': 'Home', 'url': '/'}]
        if self.category.parent:
            crumbs.append({
                'name': self.category.parent.name,
                'url':  self.category.parent.get_absolute_url()
            })
        crumbs.append({'name': self.category.name, 'url': None})
        context['breadcrumbs'] = crumbs

        return context


# ──────────────────────────────────────────────
#  BRAND
# ──────────────────────────────────────────────

class BrandView(ListView):
    """
    Brand page — all active products from a specific brand.
    e.g.  /brand/riley/  or  /brand/predator/
    """
    model = Product
    template_name = 'products/brand.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        self.brand = get_object_or_404(
            Brand,
            slug=self.kwargs['slug'],
            is_active=True
        )
        return primary_image_queryset().filter(brand=self.brand)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand']         = self.brand
        context['product_count'] = self.get_queryset().count()
        return context