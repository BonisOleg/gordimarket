"""
Моделі замовлень та CRM
"""
from __future__ import annotations

from django.db import models
from decimal import Decimal
from apps.products.models import Product


class Customer(models.Model):
    """Клієнт — агрегація контактних даних із замовлень"""

    phone = models.CharField('Телефон', max_length=20, unique=True, db_index=True)
    first_name = models.CharField('Ім\'я', max_length=100, blank=True)
    last_name = models.CharField('Прізвище', max_length=100, blank=True)
    email = models.EmailField('Email', blank=True)
    total_orders = models.PositiveIntegerField('Кількість замовлень', default=0)
    total_spent = models.DecimalField('Загальна сума', max_digits=12, decimal_places=2, default=0)
    tags = models.CharField('Теги', max_length=500, blank=True, help_text='Через кому: VIP, оптовик, etc')
    notes = models.TextField('Нотатки', blank=True)
    first_order_at = models.DateTimeField('Перше замовлення', null=True, blank=True)
    last_order_at = models.DateTimeField('Останнє замовлення', null=True, blank=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)

    class Meta:
        verbose_name = 'Клієнт'
        verbose_name_plural = 'Клієнти'
        ordering = ['-last_order_at']

    def get_full_name(self) -> str:
        parts = [p for p in [self.last_name, self.first_name] if p]
        return ' '.join(parts) or self.phone

    def recalculate_stats(self) -> None:
        """Перераховує статистику клієнта з його замовлень"""
        from django.db.models import Sum, Min, Max
        orders = self.orders.exclude(status='cancelled')
        agg = orders.aggregate(
            cnt=models.Count('id'),
            total=Sum('final_total'),
            first=Min('created_at'),
            last=Max('created_at'),
        )
        self.total_orders = agg['cnt'] or 0
        self.total_spent = agg['total'] or Decimal('0')
        self.first_order_at = agg['first']
        self.last_order_at = agg['last']
        self.save(update_fields=['total_orders', 'total_spent', 'first_order_at', 'last_order_at'])

    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.phone})"


class Order(models.Model):
    """Замовлення"""

    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('processing', 'В обробці'),
        ('pending_payment', 'Очікує оплати'),
        ('paid', 'Оплачено'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Скасовано'),
        ('refund', 'Повернення'),
        # Старі статуси для зворотньої сумісності
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Оплата на сайті'),
        ('cash_on_delivery', 'Оплата при отриманні'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ukrposhta', 'Укрпошта'),
    ]
    
    # Основна інформація
    order_number = models.CharField('Номер замовлення', max_length=20, unique=True, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Клієнт'
    )
    
    # Контактні дані
    first_name = models.CharField('Ім\'я', max_length=100)
    last_name = models.CharField('Прізвище', max_length=100)
    patronymic = models.CharField('По-батькові', max_length=100, blank=True)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    
    # Доставка
    delivery_method = models.CharField('Спосіб доставки', max_length=20, choices=DELIVERY_METHOD_CHOICES, default='nova_poshta')
    nova_poshta_city = models.CharField('Місто (НП)', max_length=300, blank=True)
    nova_poshta_city_ref = models.CharField('Місто REF (НП)', max_length=100, blank=True, help_text='Унікальний ідентифікатор міста з API НП')
    nova_poshta_warehouse = models.CharField('Відділення/Поштомат (НП)', max_length=300, blank=True)
    nova_poshta_warehouse_ref = models.CharField('Відділення REF (НП)', max_length=100, blank=True, help_text='Унікальний ідентифікатор відділення з API НП')
    ukrposhta_city = models.CharField('Місто (Укрпошта)', max_length=100, blank=True)
    ukrposhta_address = models.CharField('Адреса (Укрпошта)', max_length=200, blank=True)
    ukrposhta_index = models.CharField('Індекс (Укрпошта)', max_length=10, blank=True)
    delivery_cost = models.DecimalField('Вартість доставки', max_digits=10, decimal_places=2, default=0)
    
    # Оплата
    payment_method = models.CharField('Спосіб оплати', max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    is_paid = models.BooleanField('Оплачено', default=False)
    payment_date = models.DateTimeField('Дата оплати', null=True, blank=True)
    
    # Ціни
    subtotal_retail = models.DecimalField('Повна сума товарів', max_digits=10, decimal_places=2, default=0)
    product_discount = models.DecimalField('Знижка на товари', max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField('Промокод', max_length=50, blank=True, default='')
    promo_discount = models.DecimalField('Знижка промокоду', max_digits=10, decimal_places=2, default=0)
    final_total = models.DecimalField('Підсумкова сума', max_digits=10, decimal_places=2, default=0)
    
    # Додаткові поля
    notes = models.TextField('Примітки до замовлення', blank=True)
    admin_notes = models.TextField('Примітки адміна', blank=True)
    
    # Інтеграції
    nova_poshta_ttn = models.CharField('ТТН Нової Пошти', max_length=50, blank=True)
    payment_intent_id = models.CharField('ID платежу', max_length=100, blank=True, help_text='LiqPay або Monobank')
    monobank_parts = models.BooleanField('Оплата частинами Monobank', default=False)
    idempotency_key = models.CharField('Ключ ідемпотентності', max_length=100, blank=True, unique=True, null=True, help_text='Для запобігання подвійного оброблення webhook')
    
    # Дати
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Останнє оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new and not self.order_number:
            from django.utils import timezone
            from django.core.cache import cache
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            prefix = cache.get('order_prefix')
            if prefix is None:
                try:
                    from apps.core.models import SiteSettings
                    ss = SiteSettings.objects.only('order_prefix').first()
                    prefix = ss.order_prefix if ss else 'ORD'
                except Exception:
                    prefix = 'ORD'
                cache.set('order_prefix', prefix, 3600)
            self.order_number = f"{prefix}{timestamp}"
        super().save(*args, **kwargs)
        if is_new and self.phone:
            self._link_customer()
    
    def _link_customer(self) -> None:
        """Прив'язує або оновлює клієнта за номером телефону"""
        from django.utils import timezone as tz
        customer, created = Customer.objects.get_or_create(
            phone=self.phone,
            defaults={
                'first_name': self.first_name,
                'last_name': self.last_name,
                'email': self.email,
                'first_order_at': tz.now(),
                'last_order_at': tz.now(),
            }
        )
        if not created:
            customer.last_order_at = tz.now()
            if not customer.first_name and self.first_name:
                customer.first_name = self.first_name
            if not customer.last_name and self.last_name:
                customer.last_name = self.last_name
            if not customer.email and self.email:
                customer.email = self.email
            customer.save(update_fields=['last_order_at', 'first_name', 'last_name', 'email'])
        Order.objects.filter(pk=self.pk).update(customer=customer)
        customer.recalculate_stats()

    def get_total_cost(self):
        """Повертає загальну вартість замовлення"""
        return self.final_total + self.delivery_cost
    
    def get_customer_name(self):
        """Повертає повне ім'я клієнта"""
        parts = [self.last_name, self.first_name]
        if self.patronymic:
            parts.append(self.patronymic)
        return ' '.join(parts)
    
    def can_be_cancelled(self):
        """Чи може бути скасовано замовлення"""
        return self.status in ['pending', 'confirmed']
    
    def __str__(self):
        return f"Замовлення #{self.order_number} - {self.get_customer_name()}"


class OrderItem(models.Model):
    """Товар в замовленні"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name='Товар')
    product_name = models.CharField('Назва товару (snapshot)', max_length=200, blank=True)
    product_sku = models.CharField('Артикул (snapshot)', max_length=50, blank=True)
    quantity = models.PositiveIntegerField('Кількість')
    price = models.DecimalField('Ціна за одиницю', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Товар в замовленні'
        verbose_name_plural = 'Товари в замовленні'

    def save(self, *args, **kwargs):
        if self.product and not self.product_name:
            self.product_name = self.product.name
        if self.product and not self.product_sku:
            self.product_sku = self.product.sku
        super().save(*args, **kwargs)

    def get_cost(self):
        """Повертає вартість позиції"""
        return self.price * self.quantity

    def get_display_name(self) -> str:
        return self.product_name or (self.product.name if self.product else 'Товар видалено')

    def __str__(self):
        return f"{self.get_display_name()} x{self.quantity}"


class Newsletter(models.Model):
    """Підписка на розсилку"""
    
    email = models.EmailField('Email', unique=True)
    is_active = models.BooleanField('Активна підписка', default=True)
    created_at = models.DateTimeField('Дата підписки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Підписка на розсилку'
        verbose_name_plural = 'Підписки на розсилку'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class Promotion(models.Model):
    """Промокоди"""
    
    APPLY_TO_CHOICES = [
        ('all', 'Всі товари'),
        ('non_sale', 'Тільки не акційні'),
        ('categories', 'Обрані категорії'),
    ]
    
    name = models.CharField(
        'Назва промокоду', 
        max_length=200,
        help_text='Описова назва для внутрішнього використання (наприклад: "Літня розпродаж 2024")'
    )
    code = models.CharField(
        'Промокод', 
        max_length=50, 
        unique=True,
        help_text='Код який вводить покупець (наприклад: SUMMER2024). Буде автоматично конвертовано у верхній регістр'
    )
    discount_type = models.CharField('Тип знижки', max_length=20, choices=[
        ('percentage', 'Відсоток від суми'),
        ('fixed', 'Фіксована знижка'),
    ], default='percentage')
    discount_value = models.DecimalField('Розмір знижки', max_digits=10, decimal_places=2)
    
    apply_to = models.CharField('Застосувати до', max_length=20, choices=APPLY_TO_CHOICES, default='all')
    categories = models.ManyToManyField(
        'products.Category',
        verbose_name='Категорії',
        blank=True,
        help_text='Категорії на які діє промокод (якщо обрано "Обрані категорії")'
    )
    
    min_order_amount = models.DecimalField(
        'Мінімальна сума замовлення', 
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text='Залиште 0 якщо без обмежень'
    )
    max_uses = models.PositiveIntegerField(
        'Максимальна кількість використань', 
        null=True, 
        blank=True,
        help_text='Залиште порожнім для необмеженої кількості'
    )
    uses_count = models.PositiveIntegerField('Кількість використань', default=0, editable=False)
    
    is_active = models.BooleanField('Активний', default=True)
    start_date = models.DateTimeField('Дата початку', help_text='Промокод стане активним з цієї дати')
    end_date = models.DateTimeField('Дата закінчення', help_text='Промокод автоматично завершиться')
    
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def save(self, *args, **kwargs):
        """Автоматично конвертує код у верхній регістр"""
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Перевіряє чи дійсний промокод"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if now < self.start_date or now > self.end_date:
            return False
        
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        
        return True
    
    def can_apply_to_product(self, product):
        """Перевіряє чи можна застосувати промокод до товару"""
        if self.apply_to == 'all':
            return True
        elif self.apply_to == 'non_sale':
            return not product.is_sale_active()
        elif self.apply_to == 'categories':
            product_categories = list(product.categories.all())
            if product.primary_category:
                product_categories.append(product.primary_category)
            promo_categories = list(self.categories.all())
            return any(cat in promo_categories for cat in product_categories)
        return False
    
    def calculate_discount(self, order_total):
        """Розраховує знижку"""
        if order_total < self.min_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = order_total * (self.discount_value / 100)
        else:
            discount = self.discount_value
        
        return min(discount, order_total)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class OrderStatusHistory(models.Model):
    """Історія зміни статусів замовлення"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField('Старий статус', max_length=20, blank=True)
    new_status = models.CharField('Новий статус', max_length=20)
    changed_by = models.CharField('Змінив', max_length=100, blank=True)
    comment = models.TextField('Коментар', blank=True)
    created_at = models.DateTimeField('Час зміни', auto_now_add=True)

    class Meta:
        verbose_name = 'Зміна статусу'
        verbose_name_plural = 'Історія статусів'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"#{self.order.order_number}: {self.old_status} → {self.new_status}"


class OrderNote(models.Model):
    """Нотатки до замовлення (таймлайн)"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_notes')
    author = models.CharField('Автор', max_length=100, default='Адмін')
    text = models.TextField('Текст')
    is_internal = models.BooleanField('Внутрішня нотатка', default=True)
    created_at = models.DateTimeField('Час', auto_now_add=True)

    class Meta:
        verbose_name = 'Нотатка'
        verbose_name_plural = 'Нотатки'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"#{self.order.order_number} — {self.author}: {self.text[:50]}"


