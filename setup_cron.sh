#!/bin/bash

# Скрипт для налаштування автоматичного оновлення цін через cron
# Запуск: ./setup_cron.sh

set -e

PROJECT_DIR="/Users/sofiadmitrenko/Sites/intshop"

echo "╔════════════════════════════════════════════════════╗"
echo "║     НАЛАШТУВАННЯ АВТОМАТИЧНОГО ОНОВЛЕННЯ ЦІН       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Створюємо cron job файл
CRON_FILE="/tmp/intshop_cron.txt"

# Поточні cron jobs
crontab -l > "$CRON_FILE" 2>/dev/null || true

# Перевіряємо чи вже є наш job
if grep -q "update_prices" "$CRON_FILE"; then
    echo "⚠️  Завдання вже існує в crontab"
    echo ""
    echo "Поточні налаштування:"
    grep "update_prices" "$CRON_FILE"
    echo ""
    read -p "Замінити існуюче завдання? (y/n): " replace
    if [ "$replace" != "y" ]; then
        echo "Скасовано."
        rm "$CRON_FILE"
        exit 0
    fi
    # Видаляємо старе завдання
    grep -v "update_prices" "$CRON_FILE" > "${CRON_FILE}.tmp"
    mv "${CRON_FILE}.tmp" "$CRON_FILE"
fi

echo ""
echo "Виберіть частоту оновлення:"
echo "  1) Кожні 2 години (рекомендовано)"
echo "  2) Кожні 6 годин"
echo "  3) 1 раз на день (о 08:00)"
echo "  4) 2 рази на день (о 08:00 та 20:00)"
echo "  5) Користувацький розклад"
echo ""
read -p "Ваш вибір: " schedule

case $schedule in
    1)
        CRON_SCHEDULE="0 */2 * * *"
        DESCRIPTION="кожні 2 години"
        ;;
    2)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="кожні 6 годин"
        ;;
    3)
        CRON_SCHEDULE="0 8 * * *"
        DESCRIPTION="щодня о 08:00"
        ;;
    4)
        CRON_SCHEDULE="0 8,20 * * *"
        DESCRIPTION="щодня о 08:00 та 20:00"
        ;;
    5)
        echo ""
        echo "Введіть cron розклад (формат: хвилина година день місяць день_тижня)"
        echo "Приклад: 0 */3 * * * (кожні 3 години)"
        read -p "Розклад: " CRON_SCHEDULE
        DESCRIPTION="користувацький розклад"
        ;;
    *)
        echo "Невірний вибір!"
        rm "$CRON_FILE"
        exit 1
        ;;
esac

# Додаємо нове завдання
echo "" >> "$CRON_FILE"
echo "# Автоматичне оновлення цін з sexopt.com.ua ($DESCRIPTION)" >> "$CRON_FILE"
echo "$CRON_SCHEDULE cd $PROJECT_DIR && source venv/bin/activate && python manage.py update_prices >> /tmp/intshop_price_update.log 2>&1" >> "$CRON_FILE"

# Встановлюємо crontab
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo ""
echo "✓ Автоматичне оновлення налаштовано успішно!"
echo ""
echo "Розклад: $DESCRIPTION"
echo "Логи оновлення: /tmp/intshop_price_update.log"
echo ""
echo "Для перегляду поточних завдань: crontab -l"
echo "Для редагування завдань: crontab -e"
echo "Для видалення завдання: crontab -r"

