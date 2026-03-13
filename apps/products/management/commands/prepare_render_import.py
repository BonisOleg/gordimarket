"""
Команда для одноразового очищення БД на Render перед першим правильним імпортом
"""
from django.core.management.base import BaseCommand
from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Очищує товари/категорії на Render перед свіжим імпортом'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Підтвердження видалення (без цього не працює)'
        )
    
    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                'УВАГА: Це видалить ВСІ товари та категорії!'
            ))
            self.stdout.write('Додайте --confirm для підтвердження')
            self.stdout.write('\nПриклад: python manage.py prepare_render_import --confirm')
            return
        
        # Підрахунок перед видаленням
        product_count = Product.objects.count()
        category_count = Category.objects.count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'Поточний стан БД:')
        self.stdout.write(f'  Товарів: {product_count}')
        self.stdout.write(f'  Категорій: {category_count}')
        self.stdout.write('='*60 + '\n')
        
        # Видаляємо
        self.stdout.write('Видалення товарів...')
        Product.objects.all().delete()
        
        self.stdout.write('Видалення категорій...')
        Category.objects.all().delete()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(
            f'✓ Видалено: {product_count} товарів, {category_count} категорій'
        ))
        self.stdout.write('БД готова до імпорту!')
        self.stdout.write('='*60 + '\n')
        
        self.stdout.write('Наступні кроки:')
        self.stdout.write('  1. python manage.py import_categories')
        self.stdout.write('  2. python manage.py import_products')

