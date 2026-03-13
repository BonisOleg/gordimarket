"""
Migration: додати поля Google Merchant до Product, видалити category_type з Category
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0031_add_performance_indexes'),
    ]

    operations = [
        # Видалити category_type з Category
        migrations.RemoveField(
            model_name='category',
            name='category_type',
        ),
        # Google Merchant fields для Product
        migrations.AddField(
            model_name='product',
            name='gtin',
            field=models.CharField(blank=True, help_text='EAN-13, UPC-12 або GTIN-14', max_length=14, verbose_name='GTIN (штрих-код)'),
        ),
        migrations.AddField(
            model_name='product',
            name='mpn',
            field=models.CharField(blank=True, help_text='Manufacturer Part Number', max_length=70, verbose_name='MPN (код виробника)'),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, help_text='Бренд/виробник для Google Merchant', max_length=200, verbose_name='Бренд'),
        ),
        migrations.AddField(
            model_name='product',
            name='condition',
            field=models.CharField(
                choices=[('new', 'Новий'), ('refurbished', 'Відновлений'), ('used', 'Вживаний')],
                default='new',
                max_length=20,
                verbose_name='Стан товару'
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=7, null=True, verbose_name='Вага (кг)'),
        ),
        migrations.AddField(
            model_name='product',
            name='width',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, verbose_name='Ширина (см)'),
        ),
        migrations.AddField(
            model_name='product',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, verbose_name='Висота (см)'),
        ),
        migrations.AddField(
            model_name='product',
            name='length',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=7, null=True, verbose_name='Довжина (см)'),
        ),
    ]
