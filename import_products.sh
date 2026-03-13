#!/bin/bash

# Скрипт для імпорту товарів з постачальника
# Використання: ./import_products.sh [опції]

set -e

# Кольори для виводу
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Шлях до проекту
PROJECT_DIR="/Users/sofiadmitrenko/Sites/intshop"
cd "$PROJECT_DIR"

# Активація віртуального середовища
source venv/bin/activate

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ІМПОРТ ТОВАРІВ З ПОСТАЧАЛЬНИКА SEXOPT.COM.UA     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Меню вибору
echo "Виберіть дію:"
echo "  1) Повний імпорт (категорії + товари)"
echo "  2) Тільки категорії"
echo "  3) Тільки товари (нові та оновлення)"
echo "  4) Оновити ціни та наявність (швидке оновлення)"
echo "  5) Тестовий імпорт (10 товарів)"
echo "  0) Вихід"
echo ""
read -p "Ваш вибір: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Запускаємо повний імпорт...${NC}\n"
        python manage.py full_import
        ;;
    2)
        echo -e "\n${YELLOW}Імпортуємо категорії...${NC}\n"
        python manage.py import_categories
        ;;
    3)
        echo -e "\n${YELLOW}Імпортуємо товари...${NC}\n"
        read -p "Пропустити завантаження зображень? (y/n): " skip_images
        if [ "$skip_images" = "y" ]; then
            python manage.py import_products --skip-images
        else
            python manage.py import_products
        fi
        ;;
    4)
        echo -e "\n${YELLOW}Оновлюємо ціни та наявність...${NC}\n"
        python manage.py update_prices
        ;;
    5)
        echo -e "\n${YELLOW}Запускаємо тестовий імпорт (10 товарів без зображень)...${NC}\n"
        python manage.py import_products --limit 10 --skip-images
        ;;
    0)
        echo -e "${GREEN}До побачення!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Невірний вибір!${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ІМПОРТ ЗАВЕРШЕНО УСПІШНО!             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"

