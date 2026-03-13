"""
Management команда для очищення БД від застарілих даних
"""
from django.core.management.base import BaseCommand
from apps.products.models import Category, Product, ProductImage
from django.db.models import Count


class Command(BaseCommand):
    help = 'Очищує БД від застарілих даних перед імпортом'

    def add_arguments(self, parser):
        parser.add_argument(
            '--full',
            action='store_true',
            help='Повне очищення (видалити всі товари та категорії)'
        )

    def handle(self, *args, **options):
        full_cleanup = options['full']
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('🧹 ОЧИЩЕННЯ БАЗИ ДАНИХ'))
        self.stdout.write('='*70 + '\n')

        if full_cleanup:
            # Повне очищення
            self.stdout.write('1️⃣  Видалення всіх товарів...')
            product_count = Product.objects.count()
            if product_count > 0:
                Product.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Видалено {product_count} товарів'))
            else:
                self.stdout.write('   ✓ Товарів немає')

            self.stdout.write('\n2️⃣  Видалення всіх категорій...')
            category_count = Category.objects.count()
            if category_count > 0:
                Category.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Видалено {category_count} категорій'))
            else:
                self.stdout.write('   ✓ Категорій немає')
        else:
            # Часткове очищення (тільки порожні ЛИСТОВІ категорії та orphan images)
            self.stdout.write('1️⃣  Видалення порожніх листових категорій...')
            
            # Знаходимо категорії без товарів і без дочірніх категорій
            from django.db.models import Q
            empty_cats = Category.objects.annotate(
                product_count=Count('product'),
                children_count=Count('children')
            ).filter(
                Q(product_count=0) & Q(children_count=0)
            )
            empty_count = empty_cats.count()
            
            if empty_count > 0:
                self.stdout.write(f'   Знайдено {empty_count} порожніх листових категорій')
                empty_cats.delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Видалено {empty_count} категорій'))
            else:
                self.stdout.write('   ✓ Порожніх листових категорій немає')

            self.stdout.write('\n2️⃣  Видалення неактивних товарів...')
            inactive_products = Product.objects.filter(is_active=False, stock=0)
            inactive_count = inactive_products.count()
            
            if inactive_count > 0:
                inactive_products.delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Видалено {inactive_count} товарів'))
            else:
                self.stdout.write('   ✓ Неактивних товарів немає')

        # Orphan images
        self.stdout.write('\n3️⃣  Очищення orphan зображень...')
        try:
            orphan_images = ProductImage.objects.filter(product__isnull=True)
            orphan_count = orphan_images.count()
            if orphan_count > 0:
                orphan_images.delete()
                self.stdout.write(self.style.SUCCESS(f'   ✓ Видалено {orphan_count} зображень'))
            else:
                self.stdout.write('   ✓ Orphan зображень немає')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'   ⚠️  {e}'))

        # Підсумок
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ ОЧИЩЕННЯ ЗАВЕРШЕНО!'))
        self.stdout.write('='*70)
        self.stdout.write('\n📊 Стан БД:')
        self.stdout.write(f'   Категорій: {Category.objects.count()}')
        self.stdout.write(f'   Товарів: {Product.objects.count()}')
        self.stdout.write(f'   Активних: {Product.objects.filter(is_active=True).count()}')
        self.stdout.write('')

