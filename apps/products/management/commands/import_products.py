"""
Імпорт товарів з XML фіду постачальника (створення нових товарів)
"""
import xml.etree.ElementTree as ET
import requests
import html
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.products.models import Category, Product, ProductAttribute


class Command(BaseCommand):
    help = 'Імпортує товари з XML фіду постачальника (створює нові товари)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
            help='URL XML фіду для імпорту'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Розмір пакету для обробки'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Обмежити кількість товарів для імпорту (для тестування)'
        )

    def handle(self, *args, **options):
        url = options['url']
        batch_size = options['batch_size']
        limit = options.get('limit')

        self.stdout.write(self.style.SUCCESS('🆕 ІМПОРТ НОВИХ ТОВАРІВ'))
        self.stdout.write('='*60)

        try:
            # Завантажуємо XML
            self.stdout.write(f'📥 Завантаження даних з {url}...')
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Перевіряємо категорії
            categories_count = Category.objects.count()
            if categories_count == 0:
                self.stdout.write(self.style.ERROR('❌ Немає категорій в базі! Спочатку виконайте: python manage.py import_categories'))
                return
            
            # Створюємо індекс категорій
            categories_index = {
                cat.external_id: cat 
                for cat in Category.objects.all() 
                if cat.external_id
            }
            self.stdout.write(f'📁 Завантажено {len(categories_index)} категорій')
            
            # Знаходимо товари
            offers_elem = root.find('.//offers')
            if offers_elem is None:
                self.stdout.write(self.style.ERROR('❌ Не знайдено блок offers в XML'))
                return
            
            offers = offers_elem.findall('offer')
            total_offers = len(offers)
            
            if limit:
                offers = offers[:limit]
                self.stdout.write(f'📦 Обмеження: {limit} товарів з {total_offers}')
            else:
                self.stdout.write(f'📦 Знайдено {total_offers} товарів у фіді')
            
            # Лічильники
            created_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0

            # Обробляємо товари пакетами
            for i in range(0, len(offers), batch_size):
                batch = offers[i:i + batch_size]
                
                self.stdout.write(f'\n📦 Пакет {i//batch_size + 1}: товари {i+1}-{min(i+batch_size, len(offers))}')
                
                with transaction.atomic():
                    for offer in batch:
                        try:
                            vendor_code = self._get_text(offer, 'vendorCode')
                            if not vendor_code:
                                skipped_count += 1
                                continue

                            # Перевіряємо чи існує товар
                            product_exists = Product.objects.filter(external_id=vendor_code).exists()
                            
                            # Дані з XML
                            available = offer.get('available', 'true') == 'true'
                            price = self._get_text(offer, 'price')
                            name = self._get_text(offer, 'name')
                            description = self._get_text(offer, 'description')
                            category_id = self._get_text(offer, 'categoryId')
                            vendor = self._get_text(offer, 'vendor')
                            
                            if not name or not price:
                                skipped_count += 1
                                continue
                            
                            # Категорія
                            category = None
                            if category_id and category_id in categories_index:
                                category = categories_index[category_id]
                            
                            if not category:
                                skipped_count += 1
                                continue
                            
                            # Ціна
                            try:
                                retail_price = Decimal(price)
                            except (ValueError, TypeError):
                                skipped_count += 1
                                continue
                            
                            # Створюємо або оновлюємо товар
                            if product_exists:
                                product = Product.objects.get(external_id=vendor_code)
                                product.name = name[:200]
                                product.retail_price = retail_price
                                product.stock = 5 if available else 0
                                product.description = html.unescape(description) if description else ''
                                product.vendor_name = vendor[:200] if vendor else ''
                                product.primary_category = category
                                product.save()
                                
                                # Додаємо в categories
                                if not product.categories.filter(id=category.id).exists():
                                    product.categories.add(category)
                                
                                updated_count += 1
                            else:
                                # Генеруємо slug
                                base_slug = slugify(name)
                                slug = base_slug
                                counter = 1
                                while Product.objects.filter(slug=slug).exists():
                                    slug = f"{base_slug}-{counter}"
                                    counter += 1
                                
                                # Створюємо товар
                                product = Product.objects.create(
                                    external_id=vendor_code,
                                    name=name[:200],
                                    slug=slug,
                                    retail_price=retail_price,
                                    stock=5 if available else 0,
                                    description=html.unescape(description) if description else '',
                                    vendor_name=vendor[:200] if vendor else '',
                                    primary_category=category,
                                    is_active=True,
                                )
                                
                                # Додаємо категорію в M2M
                                product.categories.add(category)
                                created_count += 1
                            
                            # Характеристики
                            params = offer.findall('param')
                            if params:
                                ProductAttribute.objects.filter(product=product).delete()
                                
                                for param_idx, param in enumerate(params):
                                    param_name = param.get('name')
                                    param_value = param.text
                                    
                                    if param_name and param_value:
                                        ProductAttribute.objects.create(
                                            product=product,
                                            name=param_name[:100],
                                            value=param_value[:200],
                                            sort_order=param_idx,
                                        )
                            
                            # Додаємо зображення як URL
                            pictures = offer.findall('picture')
                            if pictures and not product.images.exists():
                                for idx, picture in enumerate(pictures):
                                    picture_url = picture.text
                                    if picture_url:
                                        try:
                                            from apps.products.models import ProductImage
                                            ProductImage.objects.create(
                                                product=product,
                                                image_url=picture_url,
                                                is_main=(idx == 0),
                                                sort_order=idx,
                                            )
                                        except Exception:
                                            pass

                        except Exception as e:
                            error_count += 1
                            self.stdout.write(f'    ❌ Помилка обробки товару {vendor_code}: {e}')

                # Прогрес
                processed = min(i + batch_size, len(offers))
                self.stdout.write(f'    ✅ Оброблено: {processed}/{len(offers)} '
                                f'(створено: {created_count}, оновлено: {updated_count})')

            # Підсумок
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 ІМПОРТ ЗАВЕРШЕНО!'))
            self.stdout.write(f'📊 Статистика:')
            self.stdout.write(f'   • Створено нових товарів: {created_count}')
            self.stdout.write(f'   • Оновлено існуючих: {updated_count}')
            self.stdout.write(f'   • Пропущено: {skipped_count}')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'   • Помилок: {error_count}'))
            self.stdout.write('='*60)

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка завантаження XML: {e}'))
        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка парсингу XML: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Непередбачена помилка: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def _get_text(self, element, tag):
        """Безпечно отримує текст з XML елемента"""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ''
