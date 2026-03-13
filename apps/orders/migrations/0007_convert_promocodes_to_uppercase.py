from django.db import migrations


def convert_codes_to_uppercase(apps, schema_editor):
    """Конвертує всі промокоди у верхній регістр"""
    Promotion = apps.get_model('orders', 'Promotion')
    for promo in Promotion.objects.all():
        if promo.code:
            new_code = promo.code.strip().upper()
            if new_code != promo.code:
                promo.code = new_code
                promo.save(update_fields=['code'])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_alter_promotion_code_alter_promotion_name'),
    ]

    operations = [
        migrations.RunPython(convert_codes_to_uppercase, reverse_func),
    ]

