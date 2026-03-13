#!/bin/bash
PROJECT_DIR="/Users/sofiadmitrenko/Sites/intshop"
CRON_FILE="/tmp/intshop_cron.txt"

crontab -l > "$CRON_FILE" 2>/dev/null || true

grep -v "expire_sales" "$CRON_FILE" > "${CRON_FILE}.tmp" 2>/dev/null || true
mv "${CRON_FILE}.tmp" "$CRON_FILE" 2>/dev/null || true

echo "" >> "$CRON_FILE"
echo "# Автоматичне завершення акцій (кожні 15 хвилин)" >> "$CRON_FILE"
echo "*/15 * * * * cd $PROJECT_DIR && python3 manage.py expire_sales >> /tmp/intshop_expire_sales.log 2>&1" >> "$CRON_FILE"

crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "✓ Автоматичне завершення акцій налаштовано!"
echo "Логи: /tmp/intshop_expire_sales.log"

