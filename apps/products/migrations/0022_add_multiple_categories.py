# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0020_add_postgres_search_indexes'),
    ]

    operations = [
        # Додаємо поле category_type в Category
        migrations.AddField(
            model_name='category',
            name='category_type',
            field=models.CharField(
                choices=[
                    ('general', 'Загальна'),
                    ('women', 'Для жінок'),
                    ('men', 'Для чоловіків'),
                    ('couple', 'Для пар'),
                ],
                default='general',
                max_length=20,
                verbose_name='Тип категорії'
            ),
        ),
        
        # Додаємо іконку для категорії
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name='Іконка (emoji або CSS клас)'
            ),
        ),
        
        # Додаємо нові поля для множинних категорій
        migrations.AddField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                related_name='products_new',
                to='products.category',
                verbose_name='Категорії'
            ),
        ),
        
        migrations.AddField(
            model_name='product',
            name='primary_category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='primary_products',
                to='products.category',
                verbose_name='Основна категорія'
            ),
        ),
    ]

