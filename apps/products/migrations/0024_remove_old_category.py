# Видаляємо старе поле category після міграції даних

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0023_migrate_categories_data'),
    ]

    operations = [
        # Видаляємо старе поле category
        migrations.RemoveField(
            model_name='product',
            name='category',
        ),
        
        # Перейменовуємо related_name для categories
        migrations.AlterField(
            model_name='product',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                related_name='products',
                to='products.category',
                verbose_name='Категорії'
            ),
        ),
    ]

