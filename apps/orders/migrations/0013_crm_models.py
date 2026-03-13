"""
Migration: CRM моделі — Customer, OrderStatusHistory, OrderNote,
snapshot-поля в OrderItem, customer FK в Order, нові статуси
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0012_add_nova_poshta_ref_fields'),
    ]

    operations = [
        # Customer
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(db_index=True, max_length=20, unique=True, verbose_name='Телефон')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name="Ім'я")),
                ('last_name', models.CharField(blank=True, max_length=100, verbose_name='Прізвище')),
                ('email', models.EmailField(blank=True, verbose_name='Email')),
                ('total_orders', models.PositiveIntegerField(default=0, verbose_name='Кількість замовлень')),
                ('total_spent', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Загальна сума')),
                ('tags', models.CharField(blank=True, help_text='Через кому: VIP, оптовик, etc', max_length=500, verbose_name='Теги')),
                ('notes', models.TextField(blank=True, verbose_name='Нотатки')),
                ('first_order_at', models.DateTimeField(blank=True, null=True, verbose_name='Перше замовлення')),
                ('last_order_at', models.DateTimeField(blank=True, null=True, verbose_name='Останнє замовлення')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
            ],
            options={
                'verbose_name': 'Клієнт',
                'verbose_name_plural': 'Клієнти',
                'ordering': ['-last_order_at'],
            },
        ),
        # customer FK on Order
        migrations.AddField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='orders.customer',
                verbose_name='Клієнт'
            ),
        ),
        # Snapshot fields on OrderItem
        migrations.AddField(
            model_name='orderitem',
            name='product_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='Назва товару (snapshot)'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product_sku',
            field=models.CharField(blank=True, max_length=50, verbose_name='Артикул (snapshot)'),
        ),
        # Allow product FK to be null (SET_NULL)
        migrations.AlterField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='products.product',
                verbose_name='Товар'
            ),
        ),
        # OrderStatusHistory
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=20, verbose_name='Старий статус')),
                ('new_status', models.CharField(max_length=20, verbose_name='Новий статус')),
                ('changed_by', models.CharField(blank=True, max_length=100, verbose_name='Змінив')),
                ('comment', models.TextField(blank=True, verbose_name='Коментар')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Час зміни')),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='status_history',
                    to='orders.order'
                )),
            ],
            options={
                'verbose_name': 'Зміна статусу',
                'verbose_name_plural': 'Історія статусів',
                'ordering': ['-created_at'],
            },
        ),
        # OrderNote
        migrations.CreateModel(
            name='OrderNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.CharField(default='Адмін', max_length=100, verbose_name='Автор')),
                ('text', models.TextField(verbose_name='Текст')),
                ('is_internal', models.BooleanField(default=True, verbose_name='Внутрішня нотатка')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Час')),
                ('order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='order_notes',
                    to='orders.order'
                )),
            ],
            options={
                'verbose_name': 'Нотатка',
                'verbose_name_plural': 'Нотатки',
                'ordering': ['-created_at'],
            },
        ),
    ]
