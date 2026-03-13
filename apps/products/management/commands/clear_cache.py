from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Очищає кеш категорій'

    def handle(self, *args, **options):
        cache.delete('main_categories_menu')
        self.stdout.write(self.style.SUCCESS('✅ Кеш категорій очищено'))

