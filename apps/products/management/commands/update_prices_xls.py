"""
Швидке оновлення цін та наявності з XLS файлу постачальника
Використовується для оновлення кожні 2 години
"""
import requests
import openpyxl
from io import BytesIO
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Оновлює ціни та наявність товарів з XLS файлу'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://smtm.com.ua/_prices/price-retail.xls',
            help='URL XLS файлу для оновлення'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Розмір пакету для обробки'
        )

    def handle(self, *args, **options):
        url = options['url']
        batch_size = options['batch_size']

        self.stdout.write(self.style.SUCCESS('🔄 ОНОВЛЕННЯ ЦІН ТА НАЯВНОСТІ'))
        self.stdout.write('='*60)
        self.stdout.write(f'📥 Завантаження даних з {url}...')

        try:
            # Завантажуємо XLS
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Завантажуємо workbook
            workbook = openpyxl.load_workbook(BytesIO(response.content), read_only=True)
            sheet = workbook.active
            
            # Пропускаємо заголовок (перший рядок)
            rows = list(sheet.iter_rows(min_row=2, values_only=True))
            total_rows = len(rows)
            
            self.stdout.write(f'📦 Знайдено {total_rows} записів для оновлення')
            
            # Лічильники
            updated_count = 0
            not_found_count = 0
            error_count = 0
            
            # Обробляємо пакетами
            for i in range(0, total_rows, batch_size):
                batch = rows[i:i + batch_size]
                
                with transaction.atomic():
                    for row in batch:
                        try:
                            # Структура файлу: артикул, назва, ціна, наявність
                            # Наявність: 0,1,2,3,4,5 (якщо 5 = 5 або більше)
                            if len(row) < 4:
                                continue
                            
                            vendor_code = str(row[0]).strip() if row[0] else None
                            price = row[2]
                            stock = row[3]
                            
                            if not vendor_code:
                                continue
                            
                            # Знаходимо товар
                            try:
                                product = Product.objects.get(external_id=vendor_code)
                            except Product.DoesNotExist:
                                not_found_count += 1
                                continue
                            
                            # Оновлюємо дані
                            updated = False
                            
                            # Оновлюємо ціну
                            if price:
                                try:
                                    new_price = Decimal(str(price))
                                    if product.retail_price != new_price:
                                        product.retail_price = new_price
                                        updated = True
                                except (ValueError, TypeError, Decimal.InvalidOperation):
                                    pass
                            
                            # Оновлюємо наявність
                            if stock is not None:
                                try:
                                    new_stock = int(stock)
                                    if product.stock != new_stock:
                                        product.stock = new_stock
                                        updated = True
                                except (ValueError, TypeError):
                                    pass
                            
                            if updated:
                                product.save(update_fields=['retail_price', 'stock'])
                                updated_count += 1
                        
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(f'  ❌ Помилка обробки: {e}')
                
                # Прогрес
                processed = min(i + batch_size, total_rows)
                self.stdout.write(f'  ✅ Оброблено: {processed}/{total_rows}')
            
            workbook.close()
            
            # Підсумок
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 ОНОВЛЕННЯ ЗАВЕРШЕНО!'))
            self.stdout.write(f'📊 Статистика:')
            self.stdout.write(f'   • Оновлено товарів: {updated_count}')
            self.stdout.write(f'   • Не знайдено в базі: {not_found_count}')
            if error_count > 0:
                self.stdout.write(self.style.WARNING(f'   • Помилок: {error_count}'))
            
            # Очищення кешу після оновлення
            from django.core.cache import cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS('   • Кеш очищено ✓'))
            
            self.stdout.write('='*60)

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка завантаження XLS: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Непередбачена помилка: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

