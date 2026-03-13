"""
Синхронізація товарів з постачальником з автоматичним завантаженням картинок
"""
import xml.etree.ElementTree as ET
import requests
import html
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import Category, Product, ProductAttribute
from apps.products.utils import download_product_images


class Command(BaseCommand):
    help = 'Синхронізація товарів з постачальником (ціни, наявність, картинки)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
            help='URL XML фіду для синхронізації'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Розмір пакету для обробки'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Не завантажувати картинки (тільки ціни та наявність)'
        )
        parser.add_argument(
            '--images-only',
            action='store_true',
            help='Завантажувати тільки картинки (не оновлювати ціни)'
        )

    def handle(self, *args, **options):
        url = options['url']
        batch_size = options['batch_size']
        skip_images = options['skip_images']
        images_only = options['images_only']

        action = "🖼️  КАРТИНКИ" if images_only else ("📊 ЦІНИ ТА НАЯВНІСТЬ" if skip_images else "🔄 ПОВНА СИНХРОНІЗАЦІЯ")
        self.stdout.write(self.style.SUCCESS(f'{action} ТОВАРІВ'))
        self.stdout.write('='*60)

        try:
            # Завантажуємо XML
            self.stdout.write(f'📥 Завантаження даних з {url}...')
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Знаходимо товари
            offers_elem = root.find('.//offers')
            if offers_elem is None:
                self.stdout.write(self.style.ERROR('❌ Не знайдено блок offers в XML'))
                return
            
            offers = offers_elem.findall('offer')
            total_offers = len(offers)
            self.stdout.write(f'📦 Знайдено {total_offers} товарів у фіді')
            
            if not images_only:
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

            # Лічильники
            updated_count = 0
            images_updated = 0
            skipped_count = 0
            error_count = 0

            # Обробляємо товари пакетами
            for i in range(0, total_offers, batch_size):
                batch = offers[i:i + batch_size]
                
                self.stdout.write(f'\n📦 Пакет {i//batch_size + 1}: товари {i+1}-{min(i+batch_size, total_offers)}')
                
                with transaction.atomic():
                    for offer in batch:
                        try:
                            vendor_code = self._get_text(offer, 'vendorCode')
                            if not vendor_code:
                                skipped_count += 1
                                continue

                            # Знаходимо товар в базі
                            try:
                                product = Product.objects.get(external_id=vendor_code)
                            except Product.DoesNotExist:
                                skipped_count += 1
                                continue

                            # Оновлюємо дані товару (якщо не тільки картинки)
                            if not images_only:
                                available = offer.get('available', 'true') == 'true'
                                price = self._get_text(offer, 'price')
                                name = self._get_text(offer, 'name')
                                description = self._get_text(offer, 'description')
                                category_id = self._get_text(offer, 'categoryId')
                                vendor = self._get_text(offer, 'vendor')

                                # Оновлюємо основні дані
                                updated = False
                                
                                if price:
                                    try:
                                        new_price = Decimal(price)
                                        if product.retail_price != new_price:
                                            product.retail_price = new_price
                                            updated = True
                                    except (ValueError, TypeError):
                                        pass

                                # is_active контролюється вручну адміном, не чіпаємо
                                # available впливає тільки на stock (наявність)
                                new_stock = 5 if available else 0
                                if product.stock != new_stock:
                                    product.stock = new_stock
                                    updated = True

                                if name and product.name != name[:200]:
                                    product.name = name[:200]
                                    updated = True

                                if description:
                                    clean_desc = html.unescape(description)
                                    if product.description != clean_desc:
                                        product.description = clean_desc
                                        updated = True

                                if vendor and product.vendor_name != vendor[:200]:
                                    product.vendor_name = vendor[:200]
                                    updated = True

                                # Оновлюємо категорію
                                if category_id and category_id in categories_index:
                                    new_category = categories_index[category_id]
                                    if product.primary_category != new_category:
                                        product.primary_category = new_category
                                        updated = True
                                    
                                    # Додаємо в categories якщо немає
                                    if not product.categories.filter(id=new_category.id).exists():
                                        product.categories.add(new_category)

                                if updated:
                                    product.save()
                                    updated_count += 1

                                # Оновлюємо характеристики
                                params = offer.findall('param')
                                if params:
                                    # Видаляємо старі
                                    product.attributes.all().delete()
                                    
                                    # Додаємо нові
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

                            # Завантажуємо картинки (якщо не skip_images)
                            if not skip_images:
                                pictures = offer.findall('picture')
                                if pictures:
                                    picture_urls = [p.text for p in pictures if p.text]
                                    
                                    has_images = product.images.exists()
                                    if not has_images:
                                        try:
                                            success, errors = download_product_images(
                                                product, 
                                                picture_urls, 
                                                clear_existing=False
                                            )
                                            if success > 0:
                                                images_updated += 1
                                        except Exception as e:
                                            self.stdout.write(f'    ❌ Помилка завантаження картинок для {product.name}: {e}')

                        except Exception as e:
                            error_count += 1
                            self.stdout.write(f'    ❌ Помилка обробки товару {vendor_code}: {e}')

                # Прогрес
                processed = min(i + batch_size, total_offers)
                if images_only:
                    self.stdout.write(f'    ✅ Оброблено: {processed}/{total_offers} (картинки: {images_updated})')
                else:
                    self.stdout.write(f'    ✅ Оброблено: {processed}/{total_offers} '
                                    f'(оновлено: {updated_count}, картинки: {images_updated})')

            # Підсумок
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 СИНХРОНІЗАЦІЯ ЗАВЕРШЕНА!'))
            self.stdout.write(f'📊 Статистика:')
            if not images_only:
                self.stdout.write(f'   • Оновлено товарів: {updated_count}')
            self.stdout.write(f'   • Завантажено картинок: {images_updated}')
            self.stdout.write(f'   • Пропущено: {skipped_count}')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'   • Помилок: {error_count}'))
            
            # Очищення кешу після синхронізації
            from django.core.cache import cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS('   • Кеш очищено ✓'))
            
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
