"""
Команда для швидкого додавання URL зображень без завантаження файлів
"""
import xml.etree.ElementTree as ET
import requests
from django.core.management.base import BaseCommand
from apps.products.models import Product
from apps.products.utils.image_downloader import download_product_images


class Command(BaseCommand):
    help = 'Швидке додавання URL зображень для товарів'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='https://smtm.com.ua/_prices/import-retail-ua-2.xml',
            help='URL XML фіду'
        )

    def handle(self, *args, **options):
        url = options['url']

        self.stdout.write(self.style.SUCCESS('🖼️  ШВИДКЕ ДОДАВАННЯ URL ЗОБРАЖЕНЬ'))
        self.stdout.write('='*60)

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
            self.stdout.write(f'\n📥 Завантаження XML з {url}...')
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            root = ET.fromstring(response.content)

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

            self.stdout.write(f'Знайдено картинки для {len(images_index)} товарів\n')

            added = 0
            skipped = 0

            for idx, product in enumerate(products_without_images, 1):
                if not product.external_id:
                    skipped += 1
                    continue

                picture_urls = images_index.get(product.external_id, [])
                if not picture_urls:
                    skipped += 1
                    continue

                success_count, error_count = download_product_images(
                    product, 
                    picture_urls, 
                    clear_existing=False,
                    use_urls=True
                )
                
                if success_count > 0:
                    added += 1
                    self.stdout.write(f'  [{idx}/{total_products}] {product.name[:50]}... ✅ {success_count}')
                
                if idx % 100 == 0:
                    self.stdout.write(f'  📊 Оброблено: {idx}/{total_products} | Додано: {added}')

            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 ЗАВЕРШЕНО!'))
            self.stdout.write(f'📊 Статистика:')
            self.stdout.write(f'   • Додано: {added}')
            self.stdout.write(f'   • Пропущено: {skipped}')
            self.stdout.write('='*60)

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка завантаження XML: {e}'))
        except ET.ParseError as e:
            self.stdout.write(self.style.ERROR(f'❌ Помилка парсингу XML: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Непередбачена помилка: {e}'))

    def _get_text(self, element, tag):
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ''

