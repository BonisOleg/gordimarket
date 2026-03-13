"""
Оптимізована команда для масового завантаження картинок
"""
import xml.etree.ElementTree as ET
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from apps.products.models import Product
from apps.products.utils.image_downloader import download_product_images


class Command(BaseCommand):
    help = 'Масове завантаження картинок для товарів без зображень'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
            help='URL XML фіду'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Розмір пакету для обробки (за замовчуванням: 100)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Затримка між завантаженнями в секундах (за замовчуванням: 0.1)'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Максимальна кількість повторних спроб'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=10,
            help='Кількість паралельних потоків (за замовчуванням: 10)'
        )

    def handle(self, *args, **options):
        url = options['url']
        batch_size = options['batch_size']
        delay = options['delay']
        max_retries = options['max_retries']
        workers = options['workers']

        self.stdout.write(self.style.SUCCESS('🖼️  МАСОВЕ ЗАВАНТАЖЕННЯ КАРТИНОК'))
        self.stdout.write('='*60)

        # Знаходимо товари без картинок
        products_without_images = Product.objects.filter(
            images__isnull=True,
            is_active=True,
            external_id__isnull=False
        ).distinct()
        
        total_products = products_without_images.count()
        self.stdout.write(f'Знайдено {total_products} товарів без картинок')
        
        if total_products == 0:
            self.stdout.write(self.style.SUCCESS('✅ Всі товари вже мають картинки'))
            return

        try:
            # Завантажуємо XML з картинками
            self.stdout.write(f'\n📥 Завантаження XML з {url}...')
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            # Створюємо індекс картинок по vendor_code
            offers_elem = root.find('.//offers')
            if not offers_elem:
                self.stdout.write(self.style.ERROR('❌ Не знайдено offers в XML'))
                return

            self.stdout.write('🗂️  Створення індексу картинок...')
            images_index = {}
            
            for offer in offers_elem.findall('offer'):
                vendor_code = self._get_text(offer, 'vendorCode')
                if vendor_code:
                    pictures = offer.findall('picture')
                    if pictures:
                        images_index[vendor_code] = [p.text for p in pictures if p.text]

            self.stdout.write(f'Знайдено картинки для {len(images_index)} товарів')

            def process_product(product, current_num):
                if not product.external_id:
                    return 'skipped', None
                
                picture_urls = images_index.get(product.external_id, [])
                if not picture_urls:
                    return 'skipped', None
                
                for retry in range(max_retries):
                    try:
                        success_count, error_count = download_product_images(
                            product, 
                            picture_urls, 
                            clear_existing=False
                        )
                        
                        if success_count > 0:
                            return 'success', success_count
                        elif error_count > 0:
                            return 'error', error_count
                    except Exception:
                        if retry < max_retries - 1:
                            time.sleep(delay * (retry + 1))
                
                return 'failed', None

            processed = 0
            downloaded = 0
            skipped = 0
            errors = 0

            for i in range(0, total_products, batch_size):
                batch = list(products_without_images[i:i + batch_size])
                
                self.stdout.write(f'\n📦 Пакет {i//batch_size + 1}: товари {i+1}-{min(i+batch_size, total_products)}')
                
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {}
                    for idx, product in enumerate(batch):
                        current_num = i + idx + 1
                        future = executor.submit(process_product, product, current_num)
                        futures[future] = (product, current_num)
                    
                    for future in as_completed(futures):
                        product, current_num = futures[future]
                        status, count = future.result()
                        
                        processed += 1
                        
                        if status == 'success':
                            downloaded += 1
                            self.stdout.write(f'  [{current_num}/{total_products}] {product.name[:40]}... {self.style.SUCCESS("✅")} {count}')
                        elif status == 'skipped':
                            skipped += 1
                        elif status == 'failed':
                            skipped += 1
                        elif status == 'error':
                            errors += count
                        
                        self.stdout.flush()
                
                self.stdout.write(f'  📊 Оброблено: {processed}/{total_products} | Завантажено: {downloaded} | Пропущено: {skipped}')

            # Підсумок
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 ЗАВАНТАЖЕННЯ ЗАВЕРШЕНО!'))
            self.stdout.write(f'📊 Загальна статистика:')
            self.stdout.write(f'   • Оброблено товарів: {processed}')
            self.stdout.write(f'   • Завантажено картинок: {downloaded}')
            self.stdout.write(f'   • Пропущено: {skipped}')
            if errors > 0:
                self.stdout.write(self.style.WARNING(f'   • Помилок: {errors}'))
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
