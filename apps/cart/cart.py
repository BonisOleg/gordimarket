"""
Кошик покупок без реєстрації (session-based)
"""
from decimal import Decimal
from django.conf import settings
from apps.products.models import Product


class Cart:
    """Кошик покупок"""
    
    def __init__(self, request):
        """Ініціалізація кошика"""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.user = request.user if request.user.is_authenticated else None
        self.promo_code = self.session.get('promo_code', None)
        self._products_cache = None
    
    def add(self, product, quantity=1, override_quantity=False):
        """Додавання товару в кошик"""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.get_current_price()),
                'retail_price': str(product.retail_price),
                'is_sale': product.is_sale_active()
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        self.cart[product_id]['price'] = str(product.get_current_price())
        self.cart[product_id]['retail_price'] = str(product.retail_price)
        self.cart[product_id]['is_sale'] = product.is_sale_active()
        self._clear_cache()
        self.save()
    
    def save(self):
        """Зберігання кошика в сесії"""
        self.session.modified = True
    
    def _get_products(self):
        if self._products_cache is None:
            product_ids = list(self.cart.keys())
            products = Product.objects.filter(id__in=product_ids, stock__gt=0)
            self._products_cache = {str(p.id): p for p in products}
        return self._products_cache
    
    def _clear_cache(self):
        self._products_cache = None
    
    def remove(self, product):
        """Видалення товару з кошика"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self._clear_cache()
            self.save()
    
    def __iter__(self):
        """Ітерація по товарах в кошику"""
        products_dict = self._get_products()
        
        for product_id, item_data in self.cart.items():
            product = products_dict.get(product_id)
            if not product:
                continue
            
            price = product.get_current_price()
            retail_price = product.retail_price
            quantity = item_data['quantity']
            is_sale = product.is_sale_active()
            
            yield {
                'product': product,
                'price': price,
                'retail_price': retail_price,
                'quantity': quantity,
                'is_sale': is_sale,
                'total_price': price * quantity,
                'total_retail_price': retail_price * quantity,
                'discount_amount': (retail_price - price) * quantity if is_sale else Decimal('0')
            }
    
    def __len__(self):
        """Кількість товарів в кошику"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_subtotal(self):
        """Сума товарів без промокоду"""
        products_dict = self._get_products()
        total = Decimal('0')
        for product_id, item in self.cart.items():
            product = products_dict.get(product_id)
            if product:
                total += product.get_current_price() * item['quantity']
        return total
    
    def get_total_retail_price(self):
        """Сума всіх товарів за повною ціною"""
        products_dict = self._get_products()
        total = Decimal('0')
        for product_id, item in self.cart.items():
            product = products_dict.get(product_id)
            if product:
                total += product.retail_price * item['quantity']
        return total
    
    def get_product_discount(self):
        """Загальна знижка від акційних цін"""
        return self.get_total_retail_price() - self.get_subtotal()
    
    def get_promo_discount(self):
        """Знижка від промокоду"""
        if not self.promo_code:
            return Decimal('0')
        
        from apps.orders.models import Promotion
        try:
            promotion = Promotion.objects.get(code__iexact=self.promo_code)
            if not promotion.is_valid():
                return Decimal('0')
            
            products_dict = self._get_products()
            
            applicable_total = Decimal('0')
            for product_id, item_data in self.cart.items():
                product = products_dict.get(product_id)
                if product and promotion.can_apply_to_product(product):
                    applicable_total += product.get_current_price() * item_data['quantity']
            
            if applicable_total < promotion.min_order_amount:
                return Decimal('0')
            
            if promotion.discount_type == 'percentage':
                discount = applicable_total * (promotion.discount_value / 100)
            else:
                discount = promotion.discount_value
            
            return min(discount, applicable_total)
        except Promotion.DoesNotExist:
            return Decimal('0')
    
    def get_total_price(self):
        """Загальна вартість з урахуванням промокоду"""
        return max(self.get_subtotal() - self.get_promo_discount(), Decimal('0'))
    
    def refresh_prices(self):
        """Оновлює збережені ціни в сесії до актуальних"""
        self._clear_cache()
        products_dict = self._get_products()
        for product_id in list(self.cart.keys()):
            product = products_dict.get(product_id)
            if product:
                self.cart[product_id]['price'] = str(product.get_current_price())
                self.cart[product_id]['retail_price'] = str(product.retail_price)
                self.cart[product_id]['is_sale'] = product.is_sale_active()
        self.save()
    
    def apply_promo_code(self, code):
        """Застосувати промокод"""
        from apps.orders.models import Promotion
        
        code = code.strip().upper()
        if not code:
            return False, "Введіть промокод"
        
        try:
            promotion = Promotion.objects.get(code__iexact=code)
            
            if not promotion.is_active:
                return False, "Промокод неактивний"
            
            if not promotion.is_valid():
                return False, "Промокод недійсний або закінчився"
            
            subtotal = self.get_subtotal()
            if subtotal < promotion.min_order_amount:
                return False, f"Мінімальна сума замовлення для цього промокоду: {promotion.min_order_amount} ₴"
            
            self.session['promo_code'] = promotion.code
            self.promo_code = promotion.code
            self.save()
            return True, "Промокод успішно застосовано"
            
        except Promotion.DoesNotExist:
            return False, "Промокод не знайдено"
    
    def remove_promo_code(self):
        """Видалити промокод"""
        if 'promo_code' in self.session:
            del self.session['promo_code']
        self.promo_code = None
        self.save()
    
    def clear(self):
        """Очищення кошика"""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
        self.remove_promo_code()
        self._clear_cache()
        self.save()
    
    def get_item_count(self):
        """Кількість позицій в кошику"""
        return len(self.cart)
    
    def update_quantities(self, product_quantities):
        """Оновлення кількості товарів"""
        for product_id, quantity in product_quantities.items():
            if product_id in self.cart:
                if quantity <= 0:
                    del self.cart[product_id]
                else:
                    self.cart[product_id]['quantity'] = quantity
        self._clear_cache()
        self.save()
