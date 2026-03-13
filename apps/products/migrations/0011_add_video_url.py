# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0010_cleanup_models'),
    ]

    operations = [
        # Тільки додати video_url в Product
        migrations.AddField(
            model_name='product',
            name='video_url',
            field=models.URLField(blank=True, help_text='Посилання на YouTube або Vimeo відео товару', verbose_name='Відео URL'),
        ),
    ]

