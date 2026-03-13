from django.contrib import admin
from django.utils.html import format_html
from django import forms
from django.shortcuts import redirect
from django.urls import path
from .models import Banner, TrackingPixel, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Адмін-панель для глобальних налаштувань (Singleton)"""

    fieldsets = (
        ('🏪 Ідентичність магазину', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'site_keywords'),
            'description': 'Назва та опис магазину — використовуються в мета-тегах і заголовках',
        }),
        ('📞 Контакти', {
            'fields': ('phone', 'phone_raw', 'email', 'address'),
            'description': 'Контактна інформація, що відображається на сайті',
        }),
        ('🕒 Графік роботи', {
            'fields': ('working_hours', 'day_off'),
        }),
        ('🎨 Брендинг', {
            'fields': ('logo', 'favicon', 'og_image', 'theme_color'),
            'description': 'Логотип, іконки та колір теми браузера',
        }),
        ('💬 Соціальні мережі та месенджери', {
            'fields': ('viber_number', 'telegram_link', 'whatsapp_number', 'instagram_url', 'facebook_url'),
        }),
        ('🛒 Комерція', {
            'fields': ('order_prefix', 'search_placeholder', 'free_shipping_threshold', 'copyright_text'),
            'description': 'Префікс замовлень, placeholder пошуку, поріг безкоштовної доставки',
        }),
        ('🔞 Перевірка віку', {
            'fields': ('age_verification_enabled', 'age_verification_text'),
            'classes': ('collapse',),
        }),
        ('📄 Контент сторінок', {
            'fields': ('about_content',),
            'description': 'HTML-контент для статичних сторінок',
            'classes': ('collapse',),
        }),
        ('📊 Google Tag Manager', {
            'fields': ('gtm_code',),
            'classes': ('collapse',),
        }),
        ('📊 Facebook Pixel', {
            'fields': ('fb_pixel_code',),
            'classes': ('collapse',),
        }),
        ('📊 Google Analytics', {
            'fields': ('ga_code',),
            'classes': ('collapse',),
        }),
        ('⚙️ Додатковий код (Custom Scripts)', {
            'fields': ('custom_head_code', 'custom_body_start_code', 'custom_body_end_code'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        # Забороняємо додавати більше одного запису
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Забороняємо видаляти налаштування
        return False

    def changelist_view(self, request, extra_context=None):
        # Якщо запис існує, перенаправляємо одразу на редагування
        obj = self.model.objects.first()
        if obj:
            return redirect('admin:core_sitesettings_change', obj.pk)
        return super().changelist_view(request, extra_context)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'desktop_preview', 'mobile_preview', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'alt_text']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Банер', {
            'fields': ('title', 'alt_text', 'is_active', 'order')
        }),
        ('Зображення', {
            'fields': ('desktop_image', 'mobile_image'),
        }),
        ('Посилання', {
            'fields': ('link_url',),
        }),
    )
    
    def desktop_preview(self, obj):
        if obj.desktop_image:
            return format_html('<img src="{}" alt="{}" class="admin-thumbnail-small" />', obj.desktop_image.url, obj.alt_text)
        return "Немає"
    desktop_preview.short_description = "Десктоп"
    
    def mobile_preview(self, obj):
        if obj.mobile_image:
            return format_html('<img src="{}" alt="{}" class="admin-thumbnail-small" />', obj.mobile_image.url, obj.alt_text)
        return "Немає"
    mobile_preview.short_description = "Мобільний"


class TrackingPixelAdminForm(forms.ModelForm):
    """Форма з вибором сторінок через чекбокси"""
    
    PAGE_CHOICES = [
        ('all', 'Всі сторінки (глобально)'),
        ('home', 'Головна'),
        ('delivery', 'Доставка та оплата'),
        ('returns', 'Повернення та обмін'),
        ('about', 'Про нас'),
        ('contacts', 'Контакти'),
        ('terms', 'Умови використання'),
        ('privacy', 'Політика конфіденційності'),
        ('search', 'Пошук'),
        ('product_list', 'Каталог товарів'),
        ('product_detail', 'Сторінка товару'),
        ('cart', 'Кошик'),
        ('wishlist', 'Список бажань'),
        ('order', 'Оформлення замовлення'),
    ]
    
    selected_pages = forms.MultipleChoiceField(
        choices=PAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Вибір сторінок",
        help_text="Виберіть сторінки. Якщо обрано 'Всі сторінки', інші вибори ігноруються",
        initial=['all']
    )
    
    class Meta:
        model = TrackingPixel
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Завантажити вибрані сторінки з бази
        if self.instance and self.instance.pk:
            pages_str = self.instance.pages or 'all'
            self.fields['selected_pages'].initial = [p.strip() for p in pages_str.split(',')]
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        selected = self.cleaned_data.get('selected_pages', [])
        
        # Якщо вибрано 'all', зберегти тільки 'all'
        if 'all' in selected:
            instance.pages = 'all'
        elif selected:
            instance.pages = ','.join(selected)
        else:
            instance.pages = 'all'  # За замовчуванням
        
        if commit:
            instance.save()
        return instance


@admin.register(TrackingPixel)
class TrackingPixelAdmin(admin.ModelAdmin):
    form = TrackingPixelAdminForm
    list_display = ['name', 'pixel_type', 'pixel_id', 'placement', 'pages_display', 'is_active', 'created_at']
    list_filter = ['pixel_type', 'placement', 'is_active', 'created_at']
    search_fields = ['name', 'pixel_id']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'pixel_type', 'pixel_id', 'is_active')
        }),
        ('Розміщення', {
            'fields': ('placement', 'selected_pages'),
            'description': 'Виберіть де і на яких сторінках показувати піксель'
        }),
        ('Код пікселя', {
            'fields': ('code_snippet',),
            'description': 'Вставте повний код включно з <script> тегами'
        }),
        ('Метадані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def pages_display(self, obj):
        """Показати перелік сторінок у списку"""
        if obj.pages == 'all':
            return '🌐 Всі'
        pages = obj.pages.split(',')
        return ', '.join(pages[:3]) + ('...' if len(pages) > 3 else '')
    pages_display.short_description = "Сторінки"


admin.site.site_header = "Адміністрування"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Панель управління"
