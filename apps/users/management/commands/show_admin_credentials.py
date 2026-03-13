"""
Команда для відображення даних адміністратора
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Відображає дані для входу в адмінку'

    def handle(self, *args, **options):
        User = get_user_model()
        admin = User.objects.filter(is_superuser=True).first()
        
        if admin:
            self.stdout.write(self.style.SUCCESS('='*70))
            self.stdout.write(self.style.SUCCESS('🔐 ДАНІ ДЛЯ ВХОДУ В АДМІНКУ'))
            self.stdout.write(self.style.SUCCESS('='*70))
            self.stdout.write(f'👤 Логін: {admin.username}')
            self.stdout.write(f'📧 Email: {admin.email}')
            self.stdout.write(f'📱 Телефон: {admin.phone}')
            self.stdout.write(f'🌐 URL: http://127.0.0.1:8000/admin/')
            self.stdout.write(self.style.SUCCESS('='*70))
            self.stdout.write('')
            self.stdout.write('⚠️  Якщо не пам\'ятаєте пароль, скористайтеся:')
            self.stdout.write('   python manage.py changepassword ' + admin.username)
            self.stdout.write(self.style.SUCCESS('='*70))
        else:
            self.stdout.write(self.style.ERROR('❌ Адміністратор не знайдений'))
            self.stdout.write('Створіть адміна: python manage.py createsuperuser')

