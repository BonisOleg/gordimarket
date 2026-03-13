#!/bin/bash
# Скрипт для імпорту товарів на Render після деплою
# Виконати в Render Shell: bash import_products_render.sh

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              ІМПОРТ ТОВАРІВ НА RENDER                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📦 Починаємо імпорт товарів з постачальника..."
echo ""

# Імпорт товарів з оптимізованим batch size
python manage.py import_products --batch-size 50

echo ""
echo "✅ Імпорт завершено!"
echo ""
echo "📊 Перевірка результатів:"
python manage.py shell -c "
from apps.products.models import Product, Category
print(f'Категорій: {Category.objects.count()}')
print(f'Товарів: {Product.objects.count()}')
print(f'Активних товарів: {Product.objects.filter(is_active=True).count()}')
"
echo ""
echo "🎉 Готово! Сайт готовий до роботи."

