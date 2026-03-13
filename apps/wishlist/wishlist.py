"""
Список бажань (Wishlist) без реєстрації (session-based)
"""
from django.conf import settings
from apps.products.models import Product


class Wishlist:
    """Список бажань користувача"""
    
    def __init__(self, request):
        """Ініціалізація списку бажань"""
        self.session = request.session
        wishlist = self.session.get(settings.WISHLIST_SESSION_ID)
        if not wishlist:
            wishlist = self.session[settings.WISHLIST_SESSION_ID] = []
        self.wishlist = wishlist
    
    def add(self, product):
        """Додавання товару в список бажань"""
        product_id = str(product.id)
        if product_id not in self.wishlist:
            self.wishlist.append(product_id)
            self.save()
            return True
        return False
    
    def remove(self, product):
        """Видалення товару зі списку бажань"""
        product_id = str(product.id)
        if product_id in self.wishlist:
            self.wishlist.remove(product_id)
            self.save()
            return True
        return False
    
    def save(self):
        """Зберігання списку бажань в сесії"""
        self.session.modified = True
    
    def clear(self):
        """Очищення списку бажань"""
        del self.session[settings.WISHLIST_SESSION_ID]
        self.save()
    
    def __iter__(self):
        """Ітерація по товарах в списку бажань"""
        product_ids = self.wishlist
        products = Product.objects.filter(id__in=product_ids, is_active=True, stock__gt=0).prefetch_related('images')
        
        for product in products:
            yield product
    
    def __len__(self):
        """Кількість товарів в списку бажань"""
        return len(self.wishlist)
    
    def __contains__(self, product):
        """Перевірка чи товар є в списку бажань"""
        return str(product.id) in self.wishlist
    
    def get_products(self):
        """Повертає всі товари зі списку бажань"""
        product_ids = self.wishlist
        return Product.objects.filter(id__in=product_ids, is_active=True, stock__gt=0).prefetch_related('images')

