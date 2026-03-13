# Інструкція по завершенню інтеграції Monobank та Nova Post

## ✅ Виконано:

1. ✅ Додано залежності: `cachetools`, `ecdsa`, `cryptography`
2. ✅ Створено міграцію 0010_payment_fields_update.py
3. ✅ Оновлено модель Order (idempotency_key, збільшено max_length, новий статус)
4. ✅ Створено NovaPostService (wrapper для API v2.0)
5. ✅ Створено MonobankService (з ECDSA верифікацією)
6. ✅ Переписано payment flow з pre-creation Order
7. ✅ Створено idempotent webhook handler
8. ✅ Додано fallback callback
9. ✅ Оновлено URLs

## 🔧 Виправлено (Feb 2026):

1. ✅ Додано поля `nova_poshta_city_ref` та `nova_poshta_warehouse_ref` до моделі Order
2. ✅ Оновлено форму OrderCreateForm з hidden fields для REF
3. ✅ Виправлено JavaScript autocomplete для зберігання REF
4. ✅ Виправлено API endpoints - використання правильних назв полів з getSettlements/getWarehouses
5. ✅ Реалізовано повну функцію `create_shipment()` з валідацією обов'язкових полів
6. ✅ Додано методи `get_sender_addresses()` та `get_sender_contacts()`
7. ✅ Додано admin action "📮 Створити ТТН для Нової Пошти" для автоматичного створення ТТН
8. ✅ Оновлено env.example з інструкціями щодо NOVAPOST_API_KEY

## ⚠️ Наступні кроки (в цьому порядку):

### 1. Запустити міграції локально

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Перевірити створені файли

Переконайтеся що існують:
- `apps/orders/services/__init__.py`
- `apps/orders/services/novapost.py`
- `apps/orders/services/monobank.py`
- `apps/orders/migrations/0010_payment_fields_update.py`
- `templates/orders/payment_processing.html`

### 3. Додати змінні в локальний .env

```bash
# Nova Post API
NOVAPOST_API_KEY=79cd006b68e3c92893b099586903341f

# Monobank Acquiring (тестові!)
MONOBANK_TOKEN=test_token_from_api.monobank.ua
MONOBANK_WEBHOOK_URL=http://localhost:8000/orders/payment/webhook/
```

### 4. Тестування локально

```bash
# Запустити сервер
python manage.py runserver

# Перевірити:
# 1. Створення Order з payment_method=online
# 2. Redirect на payment_init/<order_id>/
# 3. Перевірити логи
```

### 5. Тестування з ngrok (для webhook)

```bash
# В окремому терміналі
ngrok http 8000

# Скопіювати ngrok URL та додати в .env:
MONOBANK_WEBHOOK_URL=https://xxx-xxx.ngrok-free.app/orders/payment/webhook/

# Створити тестовий invoice через Monobank API
```

### 6. ВАЖЛИВО: Nova Post API endpoints

⚠️ **Endpoints в novapost.py потребують уточнення!**

Наразі використані тимчасові endpoints:
- `/dictionaries/cities` 
- `/dictionaries/warehouses`

Потрібно:
1. Зайти в офіційну документацію Nova Post API v1.0
2. Знайти актуальні endpoints для:
   - Пошуку міст
   - Отримання відділень
3. Оновити методи в `apps/orders/services/novapost.py`

### 7. Додаткові завдання (опціонально):

- [ ] Створити AJAX endpoints для autocomplete міст/відділень
- [ ] Створити novaposhta-autocomplete.js
- [ ] Оновити форму замовлення з autocomplete
- [ ] Створити management command для тестування
- [ ] Додати логування в settings (окремий logger для monobank/novapost)

## 🚀 Deployment на Render:

### 1. Додати Environment Variables в Render Dashboard:

```
NOVAPOST_API_KEY=79cd006b68e3c92893b099586903341f
MONOBANK_TOKEN=mPcv0aBKDI6i4CzLChni0Mg
MONOBANK_WEBHOOK_URL=https://your-app.onrender.com/orders/payment/webhook/
```

### 2. Перевірити що в production.py є:

```python
# Вже додано в shop/settings/base.py:
NOVAPOST_API_KEY = config('NOVAPOST_API_KEY', default='')
MONOBANK_TOKEN = config('MONOBANK_TOKEN', default='')
MONOBANK_WEBHOOK_URL = config('MONOBANK_WEBHOOK_URL', default='')
```

### 3. Deploy:

```bash
git add .
git commit -m "Add Monobank and Nova Post integration"
git push origin main
```

### 4. Після deploy — зареєструвати webhook в Monobank:

Monobank автоматично валідує webhook URL при створенні invoice.
Переконайтеся що endpoint `/orders/payment/webhook/` доступний публічно.

## 🐛 Troubleshooting:

### Помилка "Order not found" в webhook:

- Перевірте чи створився Order ДО redirect на Monobank
- Перевірте чи зберігся `payment_intent_id` в Order
- Подивіться логи: `logger.info` в views.py

### Помилка "Invalid signature":

- Перевірте що MONOBANK_TOKEN правильний
- Перевірте що публічний ключ кешується (cache.get/set працює)
- Подивіться логи в MonobankService.verify_webhook_signature()

### Nova Post JWT не генерується:

- Перевірте що NOVAPOST_API_KEY правильний
- Перевірте що endpoint `/clients/authorization` існує в v1.0 API
- Подивіться логи в NovaPostService._get_jwt()

## 📝 Примітки:

1. **Idempotency ключ** запобігає дублюванню обробки webhook
2. **select_for_update()** запобігає race condition між webhook та callback
3. **Fallback в callback** обробляє випадок коли webhook спізнився
4. Stock декрементується **ТІЛЬКИ** після успішної оплати (в webhook або fallback)

## 🔗 Корисні посилання:

- Monobank API: https://api.monobank.ua/docs/acquiring.html
- Nova Post API Portal: https://api-portal.novapost.com/en/
- Документація ECDSA: https://pypi.org/project/ecdsa/
