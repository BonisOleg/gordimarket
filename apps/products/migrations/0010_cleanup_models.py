# Очищення моделей від зайвих полів
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_category_external_id_product_external_id_and_more'),
    ]

    operations = [
        # Видаляємо зайві поля з Product
        migrations.RemoveField(
            model_name='product',
            name='min_quantity_discount',
        ),
        migrations.RemoveField(
            model_name='product',
            name='price_3_qty',
        ),
        migrations.RemoveField(
            model_name='product',
            name='price_5_qty',
        ),
        migrations.RemoveField(
            model_name='product',
            name='quantity_discount_price',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sale_end_date',
        ),
        migrations.RemoveField(
            model_name='product',
            name='sale_start_date',
        ),
        migrations.RemoveField(
            model_name='product',
            name='wholesale_price',
        ),
        
        # Оновлюємо поля
        migrations.AlterField(
            model_name='product',
            name='is_top',
            field=models.BooleanField(default=False, verbose_name='Хіт'),
        ),
        migrations.AlterField(
            model_name='product',
            name='retail_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Ціна'),
        ),
    ]

