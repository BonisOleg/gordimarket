import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_sitesettings'),
    ]

    operations = [
        # Banner: change alt_text default
        migrations.AlterField(
            model_name='banner',
            name='alt_text',
            field=models.CharField(
                default='Банер',
                help_text='Текст для accessibility та SEO',
                max_length=255,
                verbose_name='Alt текст',
            ),
        ),

        # SiteSettings: add identity fields
        migrations.AddField(
            model_name='sitesettings',
            name='site_name',
            field=models.CharField(default='My Shop', max_length=100, verbose_name='Назва магазину', help_text='Відображається в заголовках, логотипі та мета-тегах'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='site_tagline',
            field=models.CharField(blank=True, max_length=255, verbose_name='Підзаголовок / слоган'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='site_description',
            field=models.TextField(blank=True, verbose_name='Мета-опис сайту', help_text="Default <meta name='description'> для всіх сторінок"),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='site_keywords',
            field=models.CharField(blank=True, max_length=500, verbose_name='Ключові слова (meta keywords)'),
        ),

        # SiteSettings: contacts
        migrations.AddField(
            model_name='sitesettings',
            name='phone',
            field=models.CharField(blank=True, max_length=30, verbose_name='Телефон (відображення)', help_text='Наприклад: +38 (093) 700-88-06'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='phone_raw',
            field=models.CharField(blank=True, max_length=20, verbose_name='Телефон (без форматування)', help_text='Для посилань tel: та месенджерів. Наприклад: +380XXXXXXXXXX'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email магазину'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='address',
            field=models.TextField(blank=True, verbose_name='Адреса', help_text='Фізична адреса або опис доставки'),
        ),

        # SiteSettings: working hours
        migrations.AddField(
            model_name='sitesettings',
            name='working_hours',
            field=models.CharField(blank=True, default='Пн-Сб: 9:00-18:00', max_length=255, verbose_name='Графік роботи'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='day_off',
            field=models.CharField(blank=True, default='Нд: Вихідний', max_length=100, verbose_name='Вихідний день'),
        ),

        # SiteSettings: branding
        migrations.AddField(
            model_name='sitesettings',
            name='logo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='branding/',
                verbose_name='Логотип',
                help_text='Рекомендований розмір: 200×60 px, PNG з прозорістю',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'svg'])],
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='favicon',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='branding/',
                verbose_name='Favicon',
                help_text='Рекомендований розмір: 512×512 px, PNG',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'ico'])],
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='og_image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='branding/',
                verbose_name='OG зображення (для соціальних мереж)',
                help_text='Рекомендований розмір: 1200×630 px',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='theme_color',
            field=models.CharField(default='#4A90D9', max_length=7, verbose_name='Колір теми (HEX)', help_text='Використовується в meta theme-color для мобільних браузерів'),
        ),

        # SiteSettings: social / messengers
        migrations.AddField(
            model_name='sitesettings',
            name='viber_number',
            field=models.CharField(blank=True, max_length=20, verbose_name='Viber (номер)', help_text='Формат: +380XXXXXXXXX'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='telegram_link',
            field=models.CharField(blank=True, max_length=255, verbose_name='Telegram (посилання або номер)', help_text='Наприклад: https://t.me/username або +380XXXXXXXXX'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='whatsapp_number',
            field=models.CharField(blank=True, max_length=20, verbose_name='WhatsApp (номер без +)', help_text='Формат: 380XXXXXXXXX (без +)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='instagram_url',
            field=models.URLField(blank=True, verbose_name='Instagram URL'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='facebook_url',
            field=models.URLField(blank=True, verbose_name='Facebook URL'),
        ),

        # SiteSettings: commerce
        migrations.AddField(
            model_name='sitesettings',
            name='order_prefix',
            field=models.CharField(default='ORD', max_length=10, verbose_name='Префікс номера замовлення', help_text='Наприклад: ORD → ORD20250312143000'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='search_placeholder',
            field=models.CharField(default='Пошук товарів...', max_length=100, verbose_name='Placeholder у полі пошуку'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='free_shipping_threshold',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=10, verbose_name='Безкоштовна доставка від (грн)', help_text='Встановіть 0 щоб вимкнути повідомлення'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='copyright_text',
            field=models.CharField(blank=True, max_length=255, verbose_name='Текст копірайту', help_text='Якщо порожньо — використовується назва магазину'),
        ),

        # SiteSettings: features
        migrations.AddField(
            model_name='sitesettings',
            name='age_verification_enabled',
            field=models.BooleanField(default=False, verbose_name='Увімкнути перевірку віку (18+)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='age_verification_text',
            field=models.TextField(blank=True, verbose_name='Текст попередження про вік', help_text='Якщо порожньо — використовується стандартний текст'),
        ),

        # SiteSettings: content
        migrations.AddField(
            model_name='sitesettings',
            name='about_content',
            field=models.TextField(blank=True, verbose_name='Контент сторінки «Про нас»', help_text='HTML-контент. Підтримує теги <p>, <h3>, <ul>, <li>, <strong>'),
        ),
    ]
