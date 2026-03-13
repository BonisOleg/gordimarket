#!/usr/bin/env python3
"""
Тимчасовий скрипт для скидання паролю адміна (для деплою на Render)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings.production')
django.setup()

from apps.users.models import CustomUser

# Новий пароль для адміна
NEW_PASSWORD = 'ChangeMe123!'

print('\n' + '='*70)
print('🔄 СКИДАННЯ ПАРОЛЮ АДМІНІСТРАТОРА')
print('='*70 + '\n')

# Спробуємо знайти будь-якого суперюзера
superusers = CustomUser.objects.filter(is_superuser=True, is_staff=True)

if superusers.exists():
    for user in superusers:
        user.set_password(NEW_PASSWORD)
        user.is_active = True
        user.save()
        
        print(f'✅ Пароль оновлено для користувача:')
        print(f'   👤 Username: {user.username}')
        print(f'   📧 Email: {user.email}')
        print(f'   🔑 NEW Password: {NEW_PASSWORD}')
        print('-' * 70)
else:
    # Якщо немає суперюзерів - створюємо нового
    print('⚠️  Суперюзери не знайдені. Створюю нового...\n')
    
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    phone = os.getenv('ADMIN_PHONE', '+380000000000')
    
    try:
        user = CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=NEW_PASSWORD,
            phone=phone,
            first_name='Admin',
            last_name='User'
        )
        user.is_active = True
        user.email_verified = True
        user.save()
        
        print(f'✅ Новий суперюзер створено:')
        print(f'   👤 Username: {user.username}')
        print(f'   📧 Email: {user.email}')
        print(f'   🔑 Password: {NEW_PASSWORD}')
    except Exception as e:
        print(f'❌ Помилка: {e}')

print('\n' + '='*70)
print('🌐 Django Admin URL:')
print('   https://your-app-name.onrender.com/admin/')
print('='*70)
print('⚠️  ВИКОРИСТАЙТЕ ЦІ ДАНІ ДЛЯ ВХОДУ!')
print('='*70 + '\n')

