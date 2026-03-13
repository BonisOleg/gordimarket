from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from decimal import Decimal
import json
import logging
from apps.cart.cart import Cart
from apps.products.models import Product
from .models import Order, OrderItem, Promotion
from .forms import OrderCreateForm
from .services.novapost import NovaPostService
from django.conf import settings


logger = logging.getLogger(__name__)


def order_create(request):
    """Створення замовлення"""
    cart = Cart(request)
    cart.refresh_prices()
    
    if len(cart) == 0:
        messages.error(request, 'Ваш кошик порожній')
        return redirect('cart:detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                payment_method = form.cleaned_data['payment_method']
                
                # Перевірка наявності товарів
                for item in cart:
                    if item['product'].stock < item['quantity']:
                        raise ValueError(f'Недостатньо товару "{item["product"].name}" на складі')
                
                if payment_method == 'online':
                    # === НОВИЙ FLOW: Створюємо Order ДО оплати! ===
                    with transaction.atomic():
                        order = form.save(commit=False)
                        order.payment_method = 'online'
                        order.subtotal_retail = cart.get_total_retail_price()
                        order.product_discount = cart.get_product_discount()
                        order.promo_discount = cart.get_promo_discount()
                        order.final_total = cart.get_total_price()
                        order.promo_code = cart.promo_code or ''
                        order.status = 'pending_payment'  # НОВИЙ СТАТУС!
                        order.is_paid = False
                        order.save()
                        
                        # Створюємо OrderItems
                        for item in cart:
                            OrderItem.objects.create(
                                order=order,
                                product=item['product'],
                                price=item['price'],
                                quantity=item['quantity']
                            )
                        # НЕ декрементимо stock! Це зробить webhook після оплати
                    
                    # Зберігаємо order.id у сесію (для fallback)
                    request.session['pending_payment_order_id'] = order.id
                    
                    return redirect('orders:payment_init', order_id=order.id)
                
                else:
                    # Оплата при отриманні — старий flow без змін
                    with transaction.atomic():
                        order = form.save(commit=False)
                        order.subtotal_retail = cart.get_total_retail_price()
                        order.product_discount = cart.get_product_discount()
                        order.promo_discount = cart.get_promo_discount()
                        order.final_total = cart.get_total_price()
                        order.promo_code = cart.promo_code or ''
                        order.status = 'confirmed'
                        order.save()
                        
                        for item in cart:
                            OrderItem.objects.create(
                                order=order,
                                product=item['product'],
                                price=item['price'],
                                quantity=item['quantity']
                            )
                            product = item['product']
                            product.stock -= item['quantity']
                            product.save()
                        
                        if cart.promo_code:
                            try:
                                promo = Promotion.objects.get(code__iexact=cart.promo_code)
                                promo.uses_count += 1
                                promo.save()
                            except Promotion.DoesNotExist:
                                pass
                        
                        cart.clear()
                        return redirect('orders:success', order_id=order.id)
                        
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.exception(f"Order creation error: {e}")
                messages.error(request, 'Помилка при створенні замовлення')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі')
    else:
        form = OrderCreateForm()
    
    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form
    })


def order_success(request, order_id):
    """Сторінка успішного замовлення"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'orders/success.html', {'order': order})


def order_payment_init(request, order_id):
    """Ініціація онлайн оплати Monobank"""
    from .services.monobank import MonobankService
    from django.conf import settings
    from django.utils import timezone
    
    order = get_object_or_404(Order, id=order_id, status='pending_payment')
    
    # Перевіряємо чи вже створений invoice
    if order.payment_intent_id:
        messages.info(request, 'Рахунок вже створено, перенаправляємо на оплату')
        # В ідеалі тут треба отримати pageUrl з Monobank API за invoice_id
        return redirect('orders:payment_callback', order_id=order.id)
    
    monobank = MonobankService(settings.MONOBANK_TOKEN)
    
    try:
        invoice = monobank.create_invoice(
            order=order,
            webhook_url=settings.MONOBANK_WEBHOOK_URL,
            redirect_url=request.build_absolute_uri(
                reverse('orders:payment_callback', kwargs={'order_id': order.id})
            )
        )
        
        # Зберігаємо invoice_id ДО redirect!
        order.payment_intent_id = invoice['invoiceId']
        order.save(update_fields=['payment_intent_id'])
        
        logger.info(f"Redirecting to Monobank payment for order {order.order_number}")
        
        # Редірект на Monobank
        return redirect(invoice['pageUrl'])
        
    except Exception as e:
        logger.error(f"Monobank invoice creation failed for order {order.id}: {e}")
        messages.error(request, 'Помилка створення рахунку. Спробуйте пізніше.')
        order.status = 'cancelled'
        order.save()
        return redirect('orders:create')


@csrf_exempt
@require_http_methods(["POST"])
def order_payment_webhook(request):
    """Webhook від Monobank (IDEMPOTENT з select_for_update)"""
    from .services.monobank import MonobankService
    from django.conf import settings
    from django.utils import timezone
    
    # 1. Верифікація підпису
    signature = request.headers.get('X-Sign', '')
    body = request.body
    
    monobank = MonobankService(settings.MONOBANK_TOKEN)
    
    if not monobank.verify_webhook_signature(body, signature):
        logger.error("Webhook signature verification FAILED")
        return HttpResponse('Invalid signature', status=403)
    
    # 2. Парсинг webhook
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponse('Invalid JSON', status=400)
    
    invoice_id = data.get('invoiceId')
    status = data.get('status')
    modified_date = data.get('modifiedDate')
    
    logger.info(f"Webhook received: invoice={invoice_id}, status={status}, modified={modified_date}")
    
    # 3. Знаходимо Order з блокуванням (race condition protection!)
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(payment_intent_id=invoice_id)
            
            # 4. IDEMPOTENCY CHECK!
            idempotency_key = f"{invoice_id}_{status}_{modified_date}"
            if order.idempotency_key == idempotency_key:
                logger.info(f"Webhook already processed (idempotent): {idempotency_key}")
                return HttpResponse('OK (idempotent)', status=200)
            
            # 5. Обробляємо статус
            if status == 'success':
                order.is_paid = True
                order.payment_date = timezone.now()
                order.status = 'confirmed'
                order.idempotency_key = idempotency_key
                order.save()
                
                # Декрементимо stock (тільки тут!)
                for item in order.items.all():
                    product = item.product
                    product.stock -= item.quantity
                    product.save()
                
                # Промокод
                if order.promo_code:
                    try:
                        promo = Promotion.objects.get(code__iexact=order.promo_code)
                        promo.uses_count += 1
                        promo.save()
                    except Promotion.DoesNotExist:
                        pass
                
                logger.info(f"Order {order.order_number} marked as PAID")
                
            elif status == 'failure':
                order.status = 'cancelled'
                order.idempotency_key = idempotency_key
                order.save()
                logger.info(f"Order {order.order_number} marked as FAILED")
            
            return HttpResponse('OK', status=200)
    
    except Order.DoesNotExist:
        logger.error(f"Order not found for invoice_id={invoice_id}")
        return HttpResponse('Order not found', status=404)
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        return HttpResponse('Internal error', status=500)


def order_payment_callback(request, order_id):
    """Callback після повернення з Monobank (fallback якщо webhook спізнився)"""
    from .services.monobank import MonobankService
    from django.conf import settings
    from django.utils import timezone
    
    order = get_object_or_404(Order, id=order_id)
    
    # Якщо webhook вже обробив — редірект на success
    if order.is_paid:
        cart = Cart(request)
        cart.clear()
        messages.success(request, 'Оплата успішна!')
        return redirect('orders:success', order_id=order.id)
    
    # Якщо статус cancelled — помилка
    if order.status == 'cancelled':
        messages.error(request, 'Оплата не пройшла')
        return redirect('orders:create')
    
    # Webhook ще не прийшов — перевіряємо через API (fallback)
    if order.payment_intent_id:
        monobank = MonobankService(settings.MONOBANK_TOKEN)
        try:
            status_data = monobank.get_invoice_status(order.payment_intent_id)
            
            if status_data['status'] == 'success':
                # Обробляємо так само як webhook (але через transaction!)
                with transaction.atomic():
                    order = Order.objects.select_for_update().get(id=order.id)
                    
                    if not order.is_paid:  # Подвійна перевірка
                        order.is_paid = True
                        order.payment_date = timezone.now()
                        order.status = 'confirmed'
                        order.idempotency_key = f"fallback_{order.payment_intent_id}"
                        order.save()
                        
                        # Декремент stock
                        for item in order.items.all():
                            product = item.product
                            product.stock -= item.quantity
                            product.save()
                        
                        # Промокод
                        if order.promo_code:
                            try:
                                promo = Promotion.objects.get(code__iexact=order.promo_code)
                                promo.uses_count += 1
                                promo.save()
                            except Promotion.DoesNotExist:
                                pass
                
                cart = Cart(request)
                cart.clear()
                messages.success(request, 'Оплата успішна!')
                return redirect('orders:success', order_id=order.id)
            
            elif status_data['status'] in ['failure', 'expired']:
                order.status = 'cancelled'
                order.save()
                messages.error(request, 'Оплата не пройшла')
                return redirect('orders:create')
            
            else:
                # Статус ще processing — показуємо "чекайте"
                messages.info(request, 'Оплата обробляється, будь ласка, зачекайте...')
                return render(request, 'orders/payment_processing.html', {'order': order})
        
        except Exception as e:
            logger.error(f"Fallback status check failed: {e}")
            messages.error(request, 'Помилка перевірки статусу оплати')
            return redirect('orders:create')
    
    # Немає payment_intent_id — щось пішло не так
    messages.error(request, 'Дані оплати не знайдено')
    return redirect('orders:create')


@require_http_methods(["GET"])
def novaposhta_cities(request):
    """AJAX endpoint для пошуку міст Нової Пошти"""
    query = request.GET.get('q', '').strip()
    
    # Мінімум 3 символи для пошуку
    if len(query) < 3:
        return JsonResponse({'success': False, 'data': [], 'message': 'Мінімум 3 символи'})
    
    try:
        service = NovaPostService(settings.NOVAPOST_API_KEY)
        cities = service.search_cities(query, limit=50)
        
        # Форматуємо для autocomplete
        # Згідно з API getSettlements правильні поля: Ref, Description
        results = []
        for city in cities:
            results.append({
                'ref': city.get('Ref', ''),
                'label': city.get('Description', ''),
                'area': city.get('AreaDescription', ''),
                'region': city.get('RegionsDescription', '')
            })
        
        return JsonResponse({'success': True, 'data': results})
    except Exception as e:
        logger.error(f"Nova Poshta cities API error: {e}")
        return JsonResponse({'success': False, 'error': str(e), 'data': []})


@require_http_methods(["GET"])
def novaposhta_warehouses(request):
    """AJAX endpoint для отримання відділень Нової Пошти"""
    city_ref = request.GET.get('city_ref', '').strip()
    
    if not city_ref:
        return JsonResponse({'success': False, 'data': []})
    
    try:
        service = NovaPostService(settings.NOVAPOST_API_KEY)
        warehouses = service.get_warehouses(city_ref, limit=500)
        
        # Форматуємо для autocomplete
        # Згідно з API getWarehouses правильні поля: Ref, Description, Number
        results = []
        for wh in warehouses:
            results.append({
                'ref': wh.get('Ref', ''),
                'label': wh.get('Description', ''),
                'number': wh.get('Number', '')
            })
        
        return JsonResponse({'success': True, 'data': results})
    except Exception as e:
        logger.error(f"Nova Poshta warehouses API error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
