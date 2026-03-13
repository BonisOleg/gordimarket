# Оновлення індексів після зміни category на primary_category

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_remove_old_category'),
    ]

    operations = [
        # Оновлюємо індекси моделі Product
        migrations.AlterIndexTogether(
            name='product',
            index_together=set(),
        ),
    ]

