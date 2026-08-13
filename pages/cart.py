from decimal import Decimal, InvalidOperation
from .models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
        self._clean_cart()  # Fix any existing Decimal objects

    def _clean_cart(self):
        """Convert any Decimal values in session to string"""
        changed = False
        for item in self.cart.values():
            if isinstance(item.get('price'), Decimal):
                item['price'] = str(item['price'])
                changed = True
        if changed:
            self.save()

    def add(self, product, quantity=1):
        """Add product to cart or update quantity"""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)  # Always string
            }
        self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        """Mark session as modified to save changes"""
        self.session.modified = True

    def remove(self, product):
        """Remove product from cart"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update(self, product, quantity):
        """Update product quantity"""
        product_id = str(product.id)
        if product_id in self.cart:
            if quantity > 0:
                self.cart[product_id]['quantity'] = quantity
            else:
                self.remove(product)
            self.save()

    def __iter__(self):
        """Iterate over cart items and attach product objects"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        cart = {product_id: item.copy() for product_id, item in self.cart.items()}

        for product in products:
            if str(product.id) in cart:
                cart[str(product.id)]['product'] = product

        for item in cart.values():
            try:
                item['price'] = Decimal(str(item['price']))
                item['total_price'] = item['price'] * item['quantity']
                yield item
            except (InvalidOperation, KeyError):
                continue  # Skip broken items

    def __len__(self):
        """Return total number of items in cart"""
        return sum(item['quantity'] for item in self.cart.values() if isinstance(item, dict))

    def get_total_price(self):
        """Return total price of all items in cart"""
        total = Decimal('0.00')
        for item in self.cart.values():
            try:
                price = Decimal(str(item['price']))
                total += price * item['quantity']
            except (InvalidOperation, KeyError, TypeError):
                continue
        return total

    def clear(self):
        """Empty the cart"""
        if 'cart' in self.session:
            del self.session['cart']
            self.save()