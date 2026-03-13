#!/bin/bash
# Команда для видалення завантажених медіа файлів на Render
# Виконати один раз в Render Shell після деплою

echo "🗑️  Очищення медіа файлів..."

# Видаляємо всі файли в директорії products (якщо вона існує)
if [ -d "/opt/render/project/src/media/products" ]; then
    echo "Видаляю файли з /opt/render/project/src/media/products/"
    find /opt/render/project/src/media/products -type f -delete 2>/dev/null || true
    echo "✓ Директорія products очищена"
else
    echo "⚠️  Директорія /opt/render/project/src/media/products не знайдена"
fi

# Видаляємо всі файли в директорії categories (якщо вона існує)
if [ -d "/opt/render/project/src/media/categories" ]; then
    echo "Видаляю файли з /opt/render/project/src/media/categories/"
    find /opt/render/project/src/media/categories -type f -delete 2>/dev/null || true
    echo "✓ Директорія categories очищена"
else
    echo "⚠️  Директорія /opt/render/project/src/media/categories не знайдена"
fi

echo "✅ Очищення завершено!"
echo ""
echo "📝 Примітка: Тепер всі зображення зберігаються як URL і не займають місце на диску."

