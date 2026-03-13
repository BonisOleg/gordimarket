# Data migration - копіює дані зі старого category в нові поля

from django.db import migrations


def migrate_old_categories(apps, schema_editor):
    """Копіює дані зі старого ForeignKey category в нові ManyToMany categories"""
    Product = apps.get_model('products', 'Product')
    
    for product in Product.objects.all():
        if product.category_id:
            # Копіюємо стару категорію в primary_category
            product.primary_category_id = product.category_id
            product.save(update_fields=['primary_category'])
            
            # Додаємо стару категорію в categories (ManyToMany)
            product.categories.add(product.category_id)


def reverse_migration(apps, schema_editor):
    """Повертає дані назад"""
    Product = apps.get_model('products', 'Product')
    
    for product in Product.objects.all():
        if product.primary_category_id:
            product.category_id = product.primary_category_id
            product.save(update_fields=['category'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_add_multiple_categories'),
    ]

    operations = [
        migrations.RunPython(migrate_old_categories, reverse_migration),
    ]

