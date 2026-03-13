from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductReview, Category
from datetime import datetime, timedelta
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Створює тестові відгуки для товарів'

    def handle(self, *args, **options):
        reviews_data = [
            {
                'author_name': 'Ірина',
                'rating': 5,
                'text': 'Відмінна якість! Брала як подарунок подрузі, вона в захваті. Матеріал приємний на дотик. Дякую магазину за швидку обробку замовлення!',
                'category_badge': 'Комплекти',
                'product_name': 'комплект'
            },
            {
                'author_name': 'Наталія',
                'rating': 5,
                'text': 'Це моя перша покупка такого типу і я в захваті! Дуже делікатна доставка, гарна упаковка. Сам товар перевершив очікування, тепер розумію що витрачала час марно раніше 😊',
                'category_badge': 'Вібратори',
                'product_name': 'Вібратор'
            },
            {
                'author_name': 'Дмитро',
                'rating': 4,
                'text': 'Хороший товар за свою ціну. Матеріал якісний, використання зручне. В цілому гуд.',
                'category_badge': 'Мастурбатори',
                'product_name': 'Мастурбатор'
            },
            {
                'author_name': 'Марія',
                'rating': 4,
                'text': 'Вибрала цей стимулятор за відгуками і не пошкодувала. Якість хороша, ефект є. Мінус тільки один - хотілося б більше режимів.',
                'category_badge': 'Стимулятори',
                'product_name': 'стимулятор'
            },
            {
                'author_name': 'Олена',
                'rating': 5,
                'text': 'Чудовий вібратор! Компактний, потужний. Дуже задоволена покупкою, рекомендую',
                'category_badge': 'Вібратори',
                'product_name': 'Вібратор'
            },
            {
                'author_name': 'Алекс',
                'rating': 5,
                'text': 'Замовив цей вібратор для дівчини, вона в захваті! Якість супер, працює тихо, є різні режими. Упаковка дискретна. Рекомендую!',
                'category_badge': 'Вібратори',
                'product_name': 'Вібратор'
            },
            {
                'author_name': 'Галя',
                'rating': 5,
                'text': 'Чудовий лубрикант! М\'яка текстура, не липне, без запаху. Дуже задоволена, буду замовляти ще!',
                'category_badge': 'Лубриканти',
                'product_name': 'Лубрикант'
            },
            {
                'author_name': 'Анна',
                'rating': 5,
                'text': 'Брала як подарунок подрузі на день народження, вона в захваті! Матеріал приємний, все працює ідеально. Дякую за швидку доставку та дискретну упаковку!',
                'category_badge': 'Вібратори',
                'product_name': 'Вібратор'
            }
        ]

        active_products = list(Product.objects.filter(is_active=True))
        
        if not active_products:
            self.stdout.write(self.style.WARNING('Немає активних товарів. Створюю товари-заглушки...'))
            
            category = Category.objects.filter(is_active=True).first()
            if not category:
                category = Category.objects.create(
                    name='Для неї',
                    slug='for-her',
                    is_active=True,
                    sort_order=1
                )
            
            for review_data in reviews_data:
                product = Product.objects.create(
                    name=review_data['product_name'],
                    slug=f"product-{random.randint(1000, 9999)}",
                    primary_category=category,
                    retail_price=999,
                    is_active=True,
                    description=f"Товар категорії {review_data['category_badge']}"
                )
                active_products.append(product)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Створено {len(active_products)} товарів'))

        ProductReview.objects.filter(is_approved=True).delete()
        created_count = 0
        used_products = set()
        
        review_dates = [
            datetime(2025, 7, 8),
            datetime(2025, 6, 22),
            datetime(2025, 5, 18),
            datetime(2025, 4, 5),
            datetime(2025, 3, 10),
            datetime(2025, 2, 28),
            datetime(2025, 2, 3),
            datetime(2025, 1, 15),
        ]

        for idx, review_data in enumerate(reviews_data):
            products = Product.objects.filter(
                name__icontains=review_data['product_name'].split()[0],
                is_active=True
            ).exclude(id__in=used_products)
            
            product = products.first()
            
            if not product:
                remaining_products = [p for p in active_products if p.id not in used_products]
                product = random.choice(remaining_products if remaining_products else active_products)
            
            used_products.add(product.id)
            
            review = ProductReview.objects.create(
                product=product,
                author_name=review_data['author_name'],
                rating=review_data['rating'],
                text=review_data['text'],
                category_badge=review_data['category_badge'],
                is_approved=True
            )
            
            review.created_at = timezone.make_aware(review_dates[idx])
            review.save(update_fields=['created_at'])
            
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Створено {created_count} відгуків')
        )

