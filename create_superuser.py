#!/usr/bin/env python3
"""
Скрипт для автоматичного створення суперюзера на production (Render)
"""

import os
import django

def create_superuser():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings.production')
    django.setup()

    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Дані для суперюзера з environment variables
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'ChangeMe123!')
    phone = os.getenv('ADMIN_PHONE', '+380000000000')

    # Перевіряємо чи вже існує (за email або username)
    existing_user = None
    if User.objects.filter(username=username).exists():
        existing_user = User.objects.get(username=username)
        print(f'✅ Користувач {username} вже існує')
    elif User.objects.filter(email=email).exists():
        existing_user = User.objects.get(email=email)
        print(f'✅ Користувач з email {email} вже існує')
    
    if existing_user:
        # Оновлюємо дані існуючого користувача
        existing_user.username = username
        existing_user.email = email
        existing_user.set_password(password)
        existing_user.is_superuser = True
        existing_user.is_staff = True
        existing_user.is_active = True
        existing_user.phone = phone
        existing_user.save()
        print(f'🔄 Дані суперюзера оновлено')
        user = existing_user
    else:
        # Створюємо нового суперюзера
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                phone=phone,
                first_name='Admin',
                last_name='User'
            )
            print(f'✅ Створено нового суперюзера: {username}')
        except Exception as e:
            print(f'❌ Помилка створення суперюзера: {e}')
            return

    print(f'\n' + '='*70)
    print(f'🔐 ВАЖЛИВО! ДАНІ ДЛЯ ВХОДУ В DJANGO ADMIN')
    print(f'='*70)
    print(f'👤 Username (ім\'я користувача): {username}')
    print(f'📧 Email: {email}')
    print(f'🔑 Password (пароль): {password}')
    print(f'📱 Phone: {phone}')
    print(f'🌐 Admin URL: https://your-app-name.onrender.com/admin/')
    print(f'='*70)
    print(f'⚠️  ЗБЕРЕЖІТЬ ЦІ ДАНІ!')
    print(f'='*70)

if __name__ == '__main__':
    create_superuser()
