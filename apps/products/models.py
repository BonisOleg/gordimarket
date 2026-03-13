"""
Моделі товарів та категорій
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
import time


class Category(models.Model):
    """Категорії товарів з підтримкою ієрархії"""

    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    external_id = models.CharField(
        'Зовнішній ID',
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text='ID категорії в системі постачальника'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Батьківська категорія'
    )
    image = models.ImageField('Зображення', upload_to='categories/', blank=True)
    icon = models.CharField('Іконка', max_length=50, blank=True, help_text='Emoji або CSS клас')
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    # SEO поля
    meta_title = models.CharField('SEO заголовок', max_length=200, blank=True)
    meta_description = models.TextField('SEO опис', max_length=300, blank=True)
    
    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['sort_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        if not self.slug:
            return '#'
        return reverse('products:category', kwargs={'slug': self.slug})
    
    def get_all_children(self):
        """Повертає всі дочірні категорії рекурсивно"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Product(models.Model):
    """Товари"""
    
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    categories = models.ManyToManyField(Category, related_name='products', verbose_name='Категорії', blank=True)
    primary_category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='primary_products', 
        verbose_name='Основна категорія',
        help_text='Категорія для URL та основного відображення'
    )
    description = models.TextField('Опис', blank=True)
    
    # Ціна
    retail_price = models.DecimalField('Ціна', max_digits=10, decimal_places=2)
    
    # Акція (з файлів постачальника)
    is_sale = models.BooleanField('Акційний товар', default=False)
    sale_price = models.DecimalField(
        'Акційна ціна', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    sale_name = models.CharField(
        'Назва акції',
        max_length=200,
        blank=True,
        default='',
        help_text='Назва акції для відображення на стікері'
    )
    sale_start_date = models.DateTimeField(
        'Дата початку акції',
        null=True,
        blank=True,
        help_text='Залиште порожнім для необмеженої акції'
    )
    sale_end_date = models.DateTimeField(
        'Дата закінчення акції',
        null=True,
        blank=True,
        help_text='Акція автоматично завершиться після цієї дати'
    )
    
    # Бейджі (встановлюються в адмінці)
    is_top = models.BooleanField('Хіт', default=False)
    is_new = models.BooleanField('Новинка', default=False)
    
    # Додаткові поля
    sku = models.CharField('Артикул', max_length=50, unique=True, blank=True)
    external_id = models.CharField(
        'Зовнішній ID', 
        max_length=50, 
        blank=True, 
        null=True,
        unique=True,
        db_index=True,
        help_text='Артикул постачальника (vendorCode)'
    )
    vendor_name = models.CharField(
        'Постачальник', 
        max_length=200, 
        blank=True,
        help_text='Назва бренду/постачальника з фіду'
    )
    stock = models.PositiveIntegerField('Кількість на складі', default=0)
    is_active = models.BooleanField('Активний', default=True)
    is_featured = models.BooleanField('Рекомендований', default=False)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    
    # Дати
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    # Зв'язки
    tags = models.ManyToManyField(
        'ProductTag', 
        verbose_name='Теги', 
        blank=True,
        help_text='Теги для фільтрації товарів'
    )
    
    # Відео
    video_url = models.URLField(
        'Відео URL',
        blank=True,
        help_text='Посилання на YouTube або Vimeo відео товару'
    )
    
    # Google Merchant Center / фізичні параметри
    gtin = models.CharField(
        'GTIN (штрих-код)',
        max_length=14,
        blank=True,
        help_text='EAN-13, UPC-12 або GTIN-14'
    )
    mpn = models.CharField(
        'MPN (код виробника)',
        max_length=70,
        blank=True,
        help_text='Manufacturer Part Number'
    )
    brand = models.CharField(
        'Бренд',
        max_length=200,
        blank=True,
        help_text='Бренд/виробник для Google Merchant'
    )
    condition = models.CharField(
        'Стан товару',
        max_length=20,
        choices=[
            ('new', 'Новий'),
            ('refurbished', 'Відновлений'),
            ('used', 'Вживаний'),
        ],
        default='new'
    )
    weight = models.DecimalField(
        'Вага (кг)', max_digits=7, decimal_places=3, null=True, blank=True
    )
    width = models.DecimalField(
        'Ширина (см)', max_digits=7, decimal_places=1, null=True, blank=True
    )
    height = models.DecimalField(
        'Висота (см)', max_digits=7, decimal_places=1, null=True, blank=True
    )
    length = models.DecimalField(
        'Довжина (см)', max_digits=7, decimal_places=1, null=True, blank=True
    )

    # SEO поля
    meta_title = models.CharField('SEO заголовок', max_length=200, blank=True)
    meta_description = models.TextField('SEO опис', max_length=300, blank=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active', 'name']),
            models.Index(fields=['primary_category', 'is_active']),
            models.Index(fields=['is_active', 'is_sale', 'is_new', 'is_top']),
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Генерація slug з перевіркою унікальності
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Перевіряємо унікальність slug (окрім поточного об'єкта)
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Генерація SKU
        generate_sku = not self.sku
        
        if generate_sku:
            self.sku = f"TEMP{int(time.time() * 1000000)}"
        
        super().save(*args, **kwargs)
        
        if generate_sku:
            self.sku = f"BS{self.id:05d}"
            Product.objects.filter(pk=self.pk).update(sku=self.sku)
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})
    
    @property
    def main_image(self):
        """Повертає головне зображення товару"""
        return self.images.filter(is_main=True).first() or self.images.first()
    
    def is_sale_active(self):
        """Перевіряє чи активна акція (враховуючи терміни)"""
        if not self.is_sale or not self.sale_price:
            return False
        
        from django.utils import timezone
        now = timezone.now()
        
        if self.sale_start_date and now < self.sale_start_date:
            return False
        
        if self.sale_end_date and now > self.sale_end_date:
            return False
        
        return True
    
    def get_current_price(self):
        """Повертає актуальну ціну (акційну якщо є, інакше звичайну)"""
        if self.is_sale_active():
            return self.sale_price
        return self.retail_price
    
    def get_discount_percentage(self):
        """Розраховує відсоток знижки"""
        if self.is_sale_active() and self.retail_price > 0:
            discount = ((self.retail_price - self.sale_price) / self.retail_price) * 100
            return round(discount)
        return 0
    
    def get_stickers(self):
        """Повертає список активних стікерів (бейджів)"""
        stickers = []
        if self.is_top:
            stickers.append({'type': 'top', 'text': 'ТОП ПРОДАЖ', 'class': 'badge-top'})
        if self.is_new:
            stickers.append({'type': 'new', 'text': 'Новинка', 'class': 'badge-new'})
        if self.is_sale_active():
            discount = self.get_discount_percentage()
            if discount > 0:
                stickers.append({'type': 'sale', 'text': f'-{discount}%', 'class': 'badge-sale'})
            else:
                stickers.append({'type': 'sale', 'text': 'Акція', 'class': 'badge-sale'})
        if self.video_url:
            stickers.append({'type': 'video', 'text': 'ВІДЕО', 'class': 'badge-video'})
        return stickers
    
    def get_similar_products(self, limit=4):
        """Повертає схожі товари з тієї ж основної категорії"""
        if not self.primary_category:
            return Product.objects.none()
        
        return Product.objects.filter(
            primary_category=self.primary_category,
            is_active=True,
            stock__gt=0
        ).exclude(id=self.id).order_by('?')[:limit]
    
    def is_in_stock(self):
        """Перевіряє чи є товар в наявності"""
        return self.stock > 0
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Зображення товарів"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Зображення', upload_to='products/', blank=True, null=True)
    image_url = models.URLField('URL зображення', max_length=500, blank=True)
    alt_text = models.CharField('Alt текст', max_length=200, blank=True)
    is_main = models.BooleanField('Головне зображення', default=False)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    
    class Meta:
        verbose_name = 'Зображення товару'
        verbose_name_plural = 'Зображення товарів'
        ordering = ['sort_order']
        indexes = [
            models.Index(fields=['product', 'is_main']),
        ]
    
    def get_image_url(self):
        """Повертає URL зображення (завантажене або зовнішнє)"""
        if self.image:
            return self.image.url
        return self.image_url
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Зображення для {self.product.name}"


class ProductTag(models.Model):
    """Теги товарів для фільтрації"""
    
    name = models.CharField('Назва тегу', max_length=50, unique=True)
    slug = models.SlugField('URL', max_length=50, unique=True, blank=True)
    is_active = models.BooleanField('Активний', default=True)
    
    class Meta:
        verbose_name = 'Тег товару'
        verbose_name_plural = 'Теги товарів'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    """Характеристики товарів"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField('Назва характеристики', max_length=100)
    value = models.CharField('Значення', max_length=200)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    
    class Meta:
        verbose_name = 'Характеристика товару'
        verbose_name_plural = 'Характеристики товарів'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name}: {self.value}"


class ProductReview(models.Model):
    """Відгуки користувачів про товари"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='Товар')
    author_name = models.CharField('Ім\'я автора', max_length=100, default='Аноним')
    rating = models.PositiveSmallIntegerField(
        'Рейтинг',
        default=5,
        help_text='Оцінка від 1 до 5'
    )
    text = models.TextField('Текст відгуку')
    category_badge = models.CharField(
        'Бейдж категорії',
        max_length=50,
        blank=True,
        help_text='Наприклад: "Піхва", "Вакуумні стимулятори"'
    )
    is_approved = models.BooleanField('Схвалено', default=False)
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Відгук про товар'
        verbose_name_plural = 'Відгуки про товари'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_approved', '-created_at']),
            models.Index(fields=['product', 'is_approved']),
        ]
    
    def __str__(self):
        return f"Відгук від {self.author_name} на {self.product.name}"


class TopProduct(models.Model):
    """Лідери продажу на головній сторінці"""
    
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='top_product_entry',
        verbose_name='Товар',
        limit_choices_to={'is_active': True}
    )
    sort_order = models.PositiveIntegerField('Порядок відображення', default=0)
    is_active = models.BooleanField('Активний', default=True)
    created_at = models.DateTimeField('Додано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лідер продажу'
        verbose_name_plural = 'Лідери продажу'
        ordering = ['sort_order', '-created_at']
    
    def __str__(self):
        return f"Лідер продажу: {self.product.name}"
