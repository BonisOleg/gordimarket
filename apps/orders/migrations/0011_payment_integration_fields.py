from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_alter_order_status'),
    ]

    operations = [
        # Збільшуємо max_length для НП полів
        migrations.AlterField(
            model_name='order',
            name='nova_poshta_city',
            field=models.CharField('Місто (НП)', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='nova_poshta_warehouse',
            field=models.CharField('Відділення/Поштомат (НП)', max_length=300, blank=True),
        ),
        
        # Додаємо idempotency_key для запобігання дублювання
        migrations.AddField(
            model_name='order',
            name='idempotency_key',
            field=models.CharField(
                'Ключ ідемпотентності', 
                max_length=100, 
                blank=True, 
                unique=True, 
                null=True,
                help_text='Для запобігання подвійного оброблення webhook'
            ),
        ),
        
        # Додаємо новий статус до статусів
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                'Статус', 
                max_length=20, 
                choices=[
                    ('pending', 'Очікує підтвердження'),
                    ('pending_payment', 'Очікує оплати'),
                    ('confirmed', 'Підтверджено'),
                    ('cancelled', 'Скасовано'),
                    ('completed', 'Завершено'),
                ], 
                default='pending'
            ),
        ),
        
        # Індекс для швидкого пошуку
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_intent_id'], name='orders_payment_intent_idx'),
        ),
    ]
