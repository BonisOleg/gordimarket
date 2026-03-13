"""
Імпорт товарів з XLSX-файлу (формат Prom.ua / shopnow.co.ua)
Зображення зберігаються як URL — файли не завантажуються.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.products.models import Category, Product, ProductImage, ProductAttribute


# Mapping: назва підкатегорії (XLSX Назва_групи) -> назва батьківської категорії
PARENT_MAPPING: dict[str, str] = {
    # Побутова техніка
    'Электрочайники': 'Побутова техніка',
    'Блендеры, миксеры': 'Побутова техніка',
    'Тестомес': 'Побутова техніка',
    'Для завтрака': 'Побутова техніка',
    'Электрогрили': 'Побутова техніка',
    'Аэрогриль, фритюрницы': 'Побутова техніка',
    'Соковитискач': 'Побутова техніка',
    'Мясорубки': 'Побутова техніка',
    'Хлебопечки': 'Побутова техніка',
    'Кавомолка': 'Побутова техніка',
    'Вспениватели молока': 'Побутова техніка',
    'Точилки для ножей': 'Побутова техніка',
    'Капсульни': 'Побутова техніка',
    'Гейзерные': 'Побутова техніка',
    'Рожковые кофеварки': 'Побутова техніка',
    'Микроволновки': 'Побутова техніка',
    'Кухонные принадлежности': 'Побутова техніка',
    'Сковородки': 'Побутова техніка',
    'Сушки': 'Побутова техніка',
    'Вакуматоры': 'Побутова техніка',
    'Пароочистители': 'Побутова техніка',
    'Сетевой пылесос': 'Побутова техніка',
    'Паровые': 'Побутова техніка',
    'Роботи пилесоси': 'Побутова техніка',
    'Автомобильные пылесосы': 'Побутова техніка',
    'Швабри': 'Побутова техніка',
    'Гладильная доска': 'Побутова техніка',
    'Праска': 'Побутова техніка',
    'Утюги': 'Побутова техніка',
    'Вентиляторы, тепло-вентиляторы': 'Побутова техніка',
    'Увлажнители': 'Побутова техніка',
    'Осушители': 'Побутова техніка',
    # Електроніка
    'Акустика, Радио': 'Електроніка',
    'Компьютерная техника': 'Електроніка',
    'Игры, аксессуары и комплектующие для PlayStation и Xbox': 'Електроніка',
    # Інструменти
    'Инструменты, электро интрументы': 'Інструменти',
    'Акоммуляторные': 'Інструменти',
    'Перфораторы': 'Інструменти',
    'Электропилы': 'Інструменти',
    'Шуруповерти': 'Інструменти',
    'Мойка высокого давления': 'Інструменти',
    'Электро инстременты для сада': 'Інструменти',
    # Outdoor
    'палатки': 'Outdoor',
    'Туристические и садовая мебель': 'Outdoor',
    'Туристическая экипировка': 'Outdoor',
    'Гамак': 'Outdoor',
    'Байдарки, сапи, лодки': 'Outdoor',
    'Бассейны и уход за ними': 'Outdoor',
    'Спальники': 'Outdoor',
    'Для подорожей': 'Outdoor',
    'Кресла': 'Outdoor',
    # Дім і сад
    'Мебель': 'Дім і сад',
    'Светильники': 'Дім і сад',
    'Сейфы': 'Дім і сад',
    'Павильоны, теплицы': 'Дім і сад',
    'Искусственные плющи': 'Дім і сад',
    'От комаров': 'Дім і сад',
    'Для дома и хранения': 'Дім і сад',
    'Для шкафа и одежды': 'Дім і сад',
    'Для украшений и мелочей': 'Дім і сад',
    'Для транспорту': 'Дім і сад',
    'Для завтрака и ноутбука': 'Дім і сад',
    'Для косметики': 'Дім і сад',
    'Органайзеры': 'Дім і сад',
    # Дитяче
    'Игрушки': 'Дитяче',
    'Детские палатки': 'Дитяче',
    'Беговели': 'Дитяче',
    'Батуты, бассейны, качели': 'Дитяче',
    # Авто і зоо
    'Авто и гараж': 'Авто і зоо',
    'Зоотовари': 'Авто і зоо',
    # Краса і здоров'я
    'Фитнес и реабилитация': "Краса і здоров'я",
    'Для лица и тела': "Краса і здоров'я",
    'Для ног': "Краса і здоров'я",
    'Масажери, тренажери': "Краса і здоров'я",
    # Решта -> Різне
    'Новинки в магазине': 'Різне',
    "Б/в техника из Европы": 'Різне',
    'Аксессуары': 'Різне',
}

PARENT_CATEGORIES = [
    'Побутова техніка',
    'Електроніка',
    'Інструменти',
    'Outdoor',
    'Дім і сад',
    'Дитяче',
    'Авто і зоо',
    "Краса і здоров'я",
    'Різне',
]

PARENT_ICONS = {
    'Побутова техніка': '🏠',
    'Електроніка': '📱',
    'Інструменти': '🔧',
    'Outdoor': '⛺',
    'Дім і сад': '🌿',
    'Дитяче': '🧸',
    'Авто і зоо': '🚗',
    "Краса і здоров'я": '💆',
    'Різне': '📦',
}


def parse_price(value: Optional[str]) -> Optional[Decimal]:
    if not value:
        return None
    cleaned = re.sub(r'[^\d,.]', '', str(value)).replace(',', '.')
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def unique_slug(base: str, model_cls, exclude_pk=None) -> str:  # type: ignore[type-arg]
    slug = base[:200]
    counter = 1
    qs = model_cls.objects.filter(slug=slug)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.exists():
        slug = f"{base[:195]}-{counter}"
        counter += 1
        qs = model_cls.objects.filter(slug=slug)
        if exclude_pk:
            qs = qs.exclude(pk=exclude_pk)
    return slug


class Command(BaseCommand):
    help = 'Імпорт товарів з XLSX-файлу Prom.ua/shopnow'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='export-products-11-03-26_18-21-22.xlsx')
        parser.add_argument('--clear', action='store_true', help='Видалити всі товари і категорії перед імпортом')
        parser.add_argument('--limit', type=int, default=0, help='Обмежити кількість товарів (0 = всі)')
        parser.add_argument('--batch', type=int, default=50)

    def handle(self, *args, **options):
        try:
            import openpyxl
        except ImportError:
            raise CommandError('Встановіть openpyxl: pip install openpyxl')

        filepath = Path(options['file'])
        if not filepath.is_absolute():
            from django.conf import settings
            filepath = Path(settings.BASE_DIR) / filepath

        if not filepath.exists():
            raise CommandError(f'Файл не знайдено: {filepath}')

        self.stdout.write(self.style.SUCCESS(f'GORDI market — Імпорт товарів з {filepath.name}'))
        self.stdout.write('=' * 60)

        if options['clear']:
            self.stdout.write('Видалення старих даних...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING('  Старі товари та категорії видалено'))

        # Завантажуємо файл
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        wb.close()

        if options['limit']:
            rows = rows[:options['limit']]

        total = len(rows)
        self.stdout.write(f'Знайдено рядків: {total}')

        # --- Крок 1: Категорії ---
        self.stdout.write('\n[1/3] Синхронізація категорій...')
        parents = self._sync_parent_categories()
        subcats = self._sync_subcategories(rows, parents)
        self.stdout.write(f'  Батьківських: {len(parents)}, підкатегорій: {len(subcats)}')

        # --- Крок 2: Товари ---
        self.stdout.write(f'\n[2/3] Імпорт {total} товарів...')
        created = updated = skipped = errors = 0

        for i in range(0, total, options['batch']):
            batch = rows[i:i + options['batch']]
            with transaction.atomic():
                for row in batch:
                    try:
                        result = self._import_row(row, subcats)
                        if result == 'created':
                            created += 1
                        elif result == 'updated':
                            updated += 1
                        else:
                            skipped += 1
                    except Exception as exc:
                        errors += 1
                        ext_id = row[0] if row else '?'
                        self.stdout.write(self.style.ERROR(f'  Помилка [{ext_id}]: {exc}'))

            done = min(i + options['batch'], total)
            self.stdout.write(f'  {done}/{total} (створено: {created}, оновлено: {updated}, пропущено: {skipped})')

        # --- Крок 3: Очистка кешу ---
        self.stdout.write('\n[3/3] Очистка кешу...')
        from django.core.cache import cache
        cache.clear()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Імпорт завершено!'))
        self.stdout.write(f'  Створено:   {created}')
        self.stdout.write(f'  Оновлено:   {updated}')
        self.stdout.write(f'  Пропущено:  {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'  Помилок:    {errors}'))

    # ------------------------------------------------------------------ #

    def _sync_parent_categories(self) -> dict[str, Category]:
        parents: dict[str, Category] = {}
        for idx, name in enumerate(PARENT_CATEGORIES):
            slug_base = slugify(name) or f'category-{idx}'
            cat, _ = Category.objects.get_or_create(
                slug=slug_base,
                defaults={
                    'name': name,
                    'icon': PARENT_ICONS.get(name, '📦'),
                    'sort_order': idx,
                    'is_active': True,
                }
            )
            if not cat.name == name:
                cat.name = name
                cat.icon = PARENT_ICONS.get(name, '📦')
                cat.sort_order = idx
                cat.save(update_fields=['name', 'icon', 'sort_order'])
            parents[name] = cat
        return parents

    def _sync_subcategories(self, rows, parents: dict[str, Category]) -> dict[str, Category]:
        """Створює підкатегорії на основі унікальних груп у файлі"""
        seen: dict[str, dict] = {}
        for row in rows:
            group_id = str(row[17]) if row[17] is not None else ''
            group_name = str(row[18]).strip() if row[18] else ''
            if group_name and group_name not in seen:
                seen[group_name] = {'external_id': group_id}

        subcats: dict[str, Category] = {}
        for idx, (name, meta) in enumerate(seen.items()):
            parent_name = PARENT_MAPPING.get(name, 'Різне')
            parent = parents.get(parent_name) or parents.get('Різне')
            ext_id = meta['external_id'] or None
            slug_base = slugify(name) or f'subcat-{idx}'
            # Унікальність slug
            if Category.objects.filter(slug=slug_base).exists():
                existing = Category.objects.filter(slug=slug_base).first()
                if existing and existing.external_id == ext_id:
                    subcats[name] = existing
                    continue
                slug_base = unique_slug(slug_base, Category)

            cat, _ = Category.objects.get_or_create(
                external_id=ext_id,
                defaults={
                    'name': name,
                    'slug': slug_base,
                    'parent': parent,
                    'sort_order': idx,
                    'is_active': True,
                }
            )
            if cat.parent != parent:
                cat.parent = parent
                cat.save(update_fields=['parent'])
            subcats[name] = cat
        return subcats

    def _import_row(self, row, subcats: dict[str, Category]) -> str:
        """Повертає 'created', 'updated' або 'skipped'"""
        ext_id = str(row[0]).strip() if row[0] else ''
        name_uk = str(row[2]).strip() if row[2] else ''
        name_ru = str(row[1]).strip() if row[1] else ''
        name = name_uk or name_ru
        price_raw = row[8]  # Ціна
        availability = str(row[15]).strip() if row[15] else '-'
        group_name = str(row[18]).strip() if row[18] else ''
        image_urls_raw = str(row[14]).strip() if row[14] else ''
        vendor = str(row[28]).strip() if row[28] else ''
        discount_raw = row[30]  # Знижка (%)
        weight_raw = row[44]   # Вага,кг
        width_raw = row[45]    # Ширина,см
        height_raw = row[46]   # Висота,см
        length_raw = row[47]   # Довжина,см
        gtin_raw = row[42]     # Код_маркування_(GTIN)
        mpn_raw = row[43]      # Номер_пристрою_(MPN)
        desc_uk = str(row[6]).strip() if row[6] else ''
        desc_ru = str(row[5]).strip() if row[5] else ''
        description = desc_uk or desc_ru

        if not ext_id or not name:
            return 'skipped'

        price = parse_price(price_raw)
        if price is None:
            return 'skipped'

        category = subcats.get(group_name)
        if not category:
            return 'skipped'

        stock = 5 if availability == '+' else 0

        # Знижка
        sale_price = None
        is_sale = False
        if discount_raw:
            try:
                pct = Decimal(str(discount_raw).replace(',', '.').strip())
                if 0 < pct < 100:
                    sale_price = (price * (1 - pct / 100)).quantize(Decimal('0.01'))
                    is_sale = True
            except InvalidOperation:
                pass

        # Числові поля
        def to_decimal(v, places):
            if v is None:
                return None
            try:
                return Decimal(str(v).replace(',', '.')).quantize(Decimal('0.' + '0' * places))
            except InvalidOperation:
                return None

        weight = to_decimal(weight_raw, 3)
        width = to_decimal(width_raw, 1)
        height = to_decimal(height_raw, 1)
        length = to_decimal(length_raw, 1)
        gtin = str(gtin_raw).strip()[:14] if gtin_raw else ''
        mpn = str(mpn_raw).strip()[:70] if mpn_raw else ''

        created = False
        try:
            product = Product.objects.get(external_id=ext_id)
            # Оновлення
            product.name = name[:200]
            product.description = description
            product.retail_price = price
            product.stock = stock
            product.is_sale = is_sale
            product.sale_price = sale_price
            product.vendor_name = vendor[:200]
            product.brand = vendor[:200]
            product.primary_category = category
            product.weight = weight
            product.width = width
            product.height = height
            product.length = length
            if gtin:
                product.gtin = gtin
            if mpn:
                product.mpn = mpn
            product.save()
        except Product.DoesNotExist:
            slug_base = slugify(name) or f'product-{ext_id}'
            slug = unique_slug(slug_base, Product)
            product = Product.objects.create(
                external_id=ext_id,
                name=name[:200],
                slug=slug,
                description=description,
                retail_price=price,
                stock=stock,
                is_sale=is_sale,
                sale_price=sale_price,
                vendor_name=vendor[:200],
                brand=vendor[:200],
                primary_category=category,
                weight=weight,
                width=width,
                height=height,
                length=length,
                gtin=gtin,
                mpn=mpn,
                is_active=True,
            )
            created = True

        # M2M категорія
        product.categories.add(category)

        # Зображення (лише якщо ще немає)
        if image_urls_raw and not product.images.exists():
            urls = [u.strip() for u in image_urls_raw.split(',') if u.strip()]
            for idx_img, url in enumerate(urls[:10]):
                ProductImage.objects.create(
                    product=product,
                    image_url=url,
                    is_main=(idx_img == 0),
                    sort_order=idx_img,
                )

        # Характеристики (колонки 49-84: набори по 3 — Назва/Одиниця/Значення)
        attrs_data = []
        for col in range(49, 84, 3):
            attr_name = row[col] if col < len(row) else None
            attr_unit = row[col + 1] if col + 1 < len(row) else None
            attr_val = row[col + 2] if col + 2 < len(row) else None
            if attr_name and attr_val:
                unit_str = f' ({attr_unit})' if attr_unit else ''
                attrs_data.append((str(attr_name)[:100], f'{attr_val}{unit_str}'[:200]))

        if attrs_data:
            product.attributes.all().delete()
            ProductAttribute.objects.bulk_create([
                ProductAttribute(product=product, name=n, value=v, sort_order=i)
                for i, (n, v) in enumerate(attrs_data)
            ])

        return 'created' if created else 'updated'
