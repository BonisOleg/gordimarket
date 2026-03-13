"""
Тести адміністративної панелі товарів
"""
from django.test import TestCase
from apps.products.models import Category, Product


class ProductAdminTest(TestCase):
    """Тести адміністрування товарів"""
    
    def setUp(self):
        """Налаштування тестових даних"""
        self.category = Category.objects.create(name="Тестова категорія")
        self.product = Product.objects.create(
            name="Тестовий товар",
            category=self.category,
            retail_price=1000,
            stock=10
        )
    
    def test_product_creation(self):
        """Тест створення товару"""
        self.assertEqual(self.product.name, "Тестовий товар")
        self.assertEqual(self.product.retail_price, 1000)
    
    def test_current_price(self):
        """Тест отримання актуальної ціни"""
        self.assertEqual(self.product.get_current_price(), 1000)
        
        # З акцією
        self.product.is_sale = True
        self.product.sale_price = 800
        self.product.save()
        self.assertEqual(self.product.get_current_price(), 800)
