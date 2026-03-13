"""
Моделі для core додатку - банери та налаштування сайту
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from decimal import Decimal


class Banner(models.Model):
    """Модель для банерів на головній сторінці"""
    
    title = models.CharField(
        max_length=200,
        verbose_name="Назва банера",
        help_text="Назва для ідентифікації в адмін панелі"
    )
    
    # Зображення для різних пристроїв
    desktop_image = models.ImageField(
        upload_to='banners/desktop/',
        verbose_name="Зображення для десктопу",
        help_text="Розмір: 1200×400 пікселів (співвідношення 3:1)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    mobile_image = models.ImageField(
        upload_to='banners/mobile/',
        verbose_name="Зображення для мобільного",
        help_text="Розмір: 375×280 пікселів (співвідношення 1.34:1)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    # Посилання
    link_url = models.URLField(
        verbose_name="Посилання",
        help_text="URL на який переходити при натисканні на банер",
        blank=True,
        null=True
    )
    
    # Додаткові поля
    alt_text = models.CharField(
        max_length=255,
        verbose_name="Alt текст",
        help_text="Текст для accessibility та SEO",
        default="Банер"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
        help_text="Показувати банер на сайті"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортування",
        help_text="Менше число = вище в списку"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено"
    )
    
    class Meta:
        verbose_name = "Банер"
        verbose_name_plural = "Банери"
        ordering = ['order', '-created_at']
        
    def __str__(self):
        return f"{self.title} ({'Активний' if self.is_active else 'Неактивний'})"
        
    def save(self, *args, **kwargs):
        # Автоматично генеруємо alt_text якщо не заповнений
        if not self.alt_text:
            self.alt_text = f"Банер: {self.title}"
        super().save(*args, **kwargs)
        
        # Очищаємо кеш головної сторінки при зміні банерів
        from django.core.cache import cache
        cache.clear()



class SiteSettings(models.Model):
    """Глобальні налаштування сайту (singleton)"""

    # ── ІДЕНТИЧНІСТЬ ──────────────────────────────────────────────────────────
    site_name = models.CharField(
        max_length=100,
        default='GORDI market',
        verbose_name="Назва магазину",
        help_text="Відображається в заголовках, логотипі та мета-тегах",
    )
    site_tagline = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Підзаголовок / слоган",
    )
    site_description = models.TextField(
        blank=True,
        verbose_name="Мета-опис сайту",
        help_text="Default <meta name='description'> для всіх сторінок",
    )
    site_keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Ключові слова (meta keywords)",
    )

    # ── КОНТАКТИ ──────────────────────────────────────────────────────────────
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Телефон (відображення)",
        help_text="Наприклад: +38 (093) 700-88-06",
    )
    phone_raw = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон (без форматування)",
        help_text="Для посилань tel: та месенджерів. Наприклад: +380XXXXXXXXXX",
    )
    email = models.EmailField(
        blank=True,
        verbose_name="Email магазину",
    )
    address = models.TextField(
        blank=True,
        verbose_name="Адреса",
        help_text="Фізична адреса або опис доставки",
    )

    # ── ГРАФІК РОБОТИ ─────────────────────────────────────────────────────────
    working_hours = models.CharField(
        max_length=255,
        blank=True,
        default='Пн-Сб: 9:00-18:00',
        verbose_name="Графік роботи",
    )
    day_off = models.CharField(
        max_length=100,
        blank=True,
        default='Нд: Вихідний',
        verbose_name="Вихідний день",
    )

    # ── БРЕНДИНГ ──────────────────────────────────────────────────────────────
    logo = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        verbose_name="Логотип",
        help_text="Рекомендований розмір: 200×60 px, PNG з прозорістю",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'svg'])],
    )
    favicon = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        verbose_name="Favicon",
        help_text="Рекомендований розмір: 512×512 px, PNG",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'ico'])],
    )
    og_image = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        verbose_name="OG зображення (для соціальних мереж)",
        help_text="Рекомендований розмір: 1200×630 px",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
    )
    theme_color = models.CharField(
        max_length=7,
        default='#1a1a1a',
        verbose_name="Колір теми (HEX)",
        help_text="Використовується в meta theme-color для мобільних браузерів",
    )

    # ── СОЦМЕРЕЖІ / МЕСЕНДЖЕРИ ────────────────────────────────────────────────
    viber_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Viber (номер)",
        help_text="Формат: +380XXXXXXXXX",
    )
    telegram_link = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Telegram (посилання або номер)",
        help_text="Наприклад: https://t.me/username або +380XXXXXXXXX",
    )
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="WhatsApp (номер без +)",
        help_text="Формат: 380XXXXXXXXX (без +)",
    )
    instagram_url = models.URLField(
        blank=True,
        verbose_name="Instagram URL",
    )
    facebook_url = models.URLField(
        blank=True,
        verbose_name="Facebook URL",
    )

    # ── КОМЕРЦІЯ ──────────────────────────────────────────────────────────────
    order_prefix = models.CharField(
        max_length=10,
        default='ORD',
        verbose_name="Префікс номера замовлення",
        help_text="Наприклад: ORD → ORD20250312143000",
    )
    search_placeholder = models.CharField(
        max_length=100,
        default='Пошук товарів...',
        verbose_name="Placeholder у полі пошуку",
    )
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0'),
        verbose_name="Безкоштовна доставка від (грн)",
        help_text="Встановіть 0 щоб вимкнути повідомлення",
    )
    copyright_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Текст копірайту",
        help_text="Якщо порожньо — використовується назва магазину",
    )

    # ── ФУНКЦІЇ ───────────────────────────────────────────────────────────────
    age_verification_enabled = models.BooleanField(
        default=False,
        verbose_name="Увімкнути перевірку віку (18+)",
    )
    age_verification_text = models.TextField(
        blank=True,
        verbose_name="Текст попередження про вік",
        help_text="Якщо порожньо — використовується стандартний текст",
    )

    # ── КОНТЕНТ ───────────────────────────────────────────────────────────────
    about_content = models.TextField(
        blank=True,
        verbose_name="Контент сторінки «Про нас»",
        help_text="HTML-контент. Підтримує теги <p>, <h3>, <ul>, <li>, <strong>",
    )

    # ── ТРЕКІНГ ───────────────────────────────────────────────────────────────
    gtm_code = models.TextField(
        verbose_name="Код Google Tag Manager (GTM)",
        help_text="Повний код GTM (зазвичай вставляється в head)",
        blank=True,
        null=True,
    )
    fb_pixel_code = models.TextField(
        verbose_name="Код Facebook Pixel",
        help_text="Повний код Facebook Pixel",
        blank=True,
        null=True,
    )
    ga_code = models.TextField(
        verbose_name="Код Google Analytics (GA4)",
        help_text="Повний код Google Analytics",
        blank=True,
        null=True,
    )
    custom_head_code = models.TextField(
        verbose_name="Додатковий код у <head>",
        help_text="Будь-які інші скрипти або стилі для секції head",
        blank=True,
        null=True,
    )
    custom_body_start_code = models.TextField(
        verbose_name="Додатковий код на початку <body>",
        help_text="Скрипти, що вставляються одразу після відкриваючого тегу body",
        blank=True,
        null=True,
    )
    custom_body_end_code = models.TextField(
        verbose_name="Додатковий код у кінці <body>",
        help_text="Скрипти, що вставляються перед закриваючим тегом body",
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "⚙️ Налаштування сайту"

    def __str__(self) -> str:
        return f"Налаштування: {self.site_name}"

    def get_copyright(self) -> str:
        return self.copyright_text or self.site_name

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return
        super().save(*args, **kwargs)
        from django.core.cache import cache
        cache.delete('site_settings_obj')
        cache.delete('order_prefix')


class TrackingPixel(models.Model):
    """Модель для керування tracking pixels (Google Analytics, Facebook Pixel, GTM)"""
    
    PIXEL_TYPES = [
        ('facebook', 'Facebook Pixel'),
        ('google_analytics', 'Google Analytics'),
        ('google_tag_manager', 'Google Tag Manager'),
        ('custom', 'Custom Pixel'),
    ]
    
    PLACEMENT_CHOICES = [
        ('head', 'Head Section'),
        ('body_start', 'Body Start'),
        ('body_end', 'Body End'),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name="Назва пікселя",
        help_text="Описова назва для ідентифікації"
    )
    
    pixel_type = models.CharField(
        max_length=50,
        choices=PIXEL_TYPES,
        verbose_name="Тип пікселя"
    )
    
    pixel_id = models.CharField(
        max_length=100,
        verbose_name="ID пікселя",
        help_text="Наприклад: G-XXXXXXXXXX для GA, або 1234567890 для FB Pixel"
    )
    
    code_snippet = models.TextField(
        verbose_name="Код пікселя",
        help_text="Повний код включно з <script> тегами"
    )
    
    placement = models.CharField(
        max_length=20,
        choices=PLACEMENT_CHOICES,
        default='head',
        verbose_name="Розташування",
        help_text="Де вставити код на сторінці"
    )
    
    pages = models.CharField(
        max_length=500,
        default='all',
        verbose_name="Сторінки",
        help_text="Розділені комами: 'all' для всіх, або home,delivery,about..."
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
        help_text="Чи працює піксель зараз"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено"
    )
    
    class Meta:
        verbose_name = "Tracking Pixel"
        verbose_name_plural = "📊 Tracking Pixels"
        ordering = ['-created_at']
        unique_together = [['pixel_type', 'pixel_id']]
    
    def __str__(self):
        return f"{self.name} ({self.get_pixel_type_display()})"
