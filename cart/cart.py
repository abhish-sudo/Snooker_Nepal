from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from products.models import Product


class Cart:
    """
    Session-based shopping cart.
    Can be upgraded to a database model for persistent carts later.
    """

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart: Dict[str, Any] = cart

    def add(self, product, quantity=1, override_quantity=False, variant=None):
        """Add a product to the cart or update its quantity."""
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
                'variant_id': str(variant.id) if variant else None,
                'variant_name': variant.name if variant else '',
                'variant_sku': variant.sku if variant else '',
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.save()

    def save(self):
        """Mark the session as modified to ensure it gets saved."""
        self.session.modified = True

    def remove(self, product):
        """Remove a product from the cart."""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product_id, quantity):
        """Update the quantity of a specific cart item."""
        product_id = str(product_id)
        if product_id in self.cart:
            if quantity > 0:
                self.cart[product_id]['quantity'] = quantity
            else:
                del self.cart[product_id]
            self.save()

    def __iter__(self):
        """
        Iterate over cart items, fetching product and variant objects
        from the database. Yields enriched item dicts.
        """
        from products.models import ProductVariant

        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = self.cart.copy()

        # Attach product objects
        for product in products:
            cart[str(product.id)]['product'] = product

        # Attach variant objects
        for item in cart.values():
            variant_id = item.get('variant_id')
            if variant_id:
                try:
                    item['variant'] = ProductVariant.objects.get(id=variant_id)
                except ProductVariant.DoesNotExist:
                    item['variant'] = None
            else:
                item['variant'] = None

            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Return total number of items (sum of all quantities)."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of all items in NPR."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def get_item_count(self):
        """Get total number of items — same as __len__."""
        return len(self)

    def clear(self):
        """Remove the entire cart from the session."""
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_items(self):
        """Return all cart items as a list."""
        return list(self.__iter__())