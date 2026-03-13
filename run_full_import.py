#!/usr/bin/env python3
"""
Повний процес імпорту товарів після виправлень
Використовується для чистого імпорту після виправлення всіх проблем
"""
import os
import sys
import django
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings.development')
django.setup()

from django.core.management import call_command


def print_header(text):
    """Красиво виводить заголовок"""
    print('\n' + '='*70)
    print(f'{text:^70}')
    print('='*70 + '\n')


def run_step(step_num, title, func):
    """Виконує крок з обробкою помилок"""
    print_header(f'Крок {step_num}: {title}')
    try:
        func()
        print(f'\n✅ Крок {step_num} завершено успішно!')
        return True
    except Exception as e:
        print(f'\n❌ Помилка на кроці {step_num}: {e}')
        import traceback
        traceback.print_exc()
        return False


def step1_cleanup():
    """Крок 1: Очищення дублікатів"""
    print('🧹 Виконую очищення дублікатів категорій...')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cleanup_script = os.path.join(script_dir, 'cleanup_duplicates.py')
    subprocess.run([sys.executable, cleanup_script], check=True)


def step2_import_categories():
    """Крок 2: Імпорт категорій"""
    print('📁 Імпортую категорії з XML фіду...')
    call_command(
        'import_categories',
        url='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
        verbosity=1
    )


def step3_import_products():
    """Крок 3: Імпорт товарів"""
    print('📦 Імпортую товари з XML фіду...')
    call_command(
        'import_products',
        url='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
        verbosity=1
    )


def step4_sync():
    """Крок 4: Синхронізація для перевірки"""
    print('🔄 Виконую синхронізацію для перевірки...')
    call_command(
        'sync_products',
        url='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
        batch_size=50,
        verbosity=1
    )


def step5_verify():
    """Крок 5: Перевірка результатів"""
    from apps.products.models import Category, Product
    from django.db.models import Count
    
    print('📊 Перевірка результатів...\n')
    
    # Статистика категорій
    total_cats = Category.objects.count()
    active_cats = Category.objects.filter(is_active=True).count()
    parent_cats = Category.objects.filter(parent__isnull=True).count()
    
    print(f'📁 Категорії:')
    print(f'   • Всього: {total_cats}')
    print(f'   • Активних: {active_cats}')
    print(f'   • Головних: {parent_cats}')
    
    # Перевірка дублікатів
    duplicates = Category.objects.values('name').annotate(
        count=Count('id')
    ).filter(count__gt=1).count()
    
    if duplicates > 0:
        print(f'   ⚠️  УВАГА: Знайдено {duplicates} груп дублікатів!')
    else:
        print(f'   ✅ Дублікатів не знайдено')
    
    # Статистика товарів
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    in_stock = Product.objects.filter(stock__gt=0).count()
    no_primary = Product.objects.filter(primary_category__isnull=True).count()
    
    print(f'\n📦 Товари:')
    print(f'   • Всього: {total_products}')
    print(f'   • Активних: {active_products}')
    print(f'   • В наявності: {in_stock}')
    
    if no_primary > 0:
        print(f'   ⚠️  УВАГА: {no_primary} товарів без primary_category!')
    else:
        print(f'   ✅ Всі товари мають primary_category')
    
    # Товари по категоріях
    print(f'\n📂 Топ-5 категорій за кількістю товарів:')
    top_cats = Category.objects.annotate(
        product_count=Count('products', distinct=True)
    ).filter(product_count__gt=0).order_by('-product_count')[:5]
    
    for cat in top_cats:
        print(f'   • {cat.name}: {cat.product_count} товарів')


def main():
    """Головна функція"""
    print_header('🚀 ПОВНИЙ ІМПОРТ ТОВАРІВ ТА КАТЕГОРІЙ')
    
    print('Цей скрипт виконає повний процес імпорту:')
    print('1. Очищення дублікатів категорій')
    print('2. Імпорт категорій з XML')
    print('3. Імпорт товарів з XML')
    print('4. Синхронізація для перевірки')
    print('5. Перевірка результатів')
    print()
    
    response = input('Розпочати? (так/ні): ').strip().lower()
    if response not in ['так', 'yes', 'y', 'т']:
        print('❌ Скасовано користувачем')
        return
    
    steps = [
        (1, 'Очищення дублікатів', step1_cleanup),
        (2, 'Імпорт категорій', step2_import_categories),
        (3, 'Імпорт товарів', step3_import_products),
        (4, 'Синхронізація', step4_sync),
        (5, 'Перевірка результатів', step5_verify),
    ]
    
    for step_num, title, func in steps:
        success = run_step(step_num, title, func)
        if not success:
            print(f'\n❌ Зупинено на кроці {step_num}')
            return
    
    print_header('🎉 ІМПОРТ ЗАВЕРШЕНО УСПІШНО!')
    print('Тепер можете:')
    print('1. Перевірити категорії в адмінці: /admin/products/category/')
    print('2. Перевірити товари в адмінці: /admin/products/product/')
    print('3. Перевірити відображення на сайті')
    print('4. Налаштувати cron: ./setup_sync_cron.sh')
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n❌ Скасовано користувачем (Ctrl+C)')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Непередбачена помилка: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

