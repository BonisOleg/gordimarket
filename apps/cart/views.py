from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from apps.products.models import Product
from .cart import Cart
import json


@ensure_csrf_cookie
def cart_detail(request):
    """Перегляд кошика"""
    cart = Cart(request)
    cart.refresh_prices()
    return render(request, 'cart/detail.html', {'cart': cart})


@ensure_csrf_cookie
def cart_count(request):
    """API для отримання кількості товарів у кошику"""
    cart = Cart(request)
    return JsonResponse({'count': len(cart)})


@require_POST
def cart_add(request, product_id):
    """Додавання товару в кошик"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Перевірка наявності на складі
    if product.stock <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Товару немає в наявності',
                'cart_count': len(cart)
            }, status=400)
        return redirect('cart:detail')
    
    quantity = 1
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (json.JSONDecodeError, ValueError, KeyError):
            quantity = 1
    else:
        quantity = int(request.POST.get('quantity', 1))
    
    # Перевірка чи достатньо товару на складі
    if quantity > product.stock:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': False,
                'message': f'На складі доступно лише {product.stock} шт.',
                'cart_count': len(cart)
            }, status=400)
        return redirect('cart:detail')
    
    cart.add(product=product, quantity=quantity)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': 'Товар додано до кошика',
            'cart_count': len(cart)
        })
    
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    """Видалення товару з кошика"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': 'Товар видалено з кошика',
            'cart_count': len(cart)
        })
    
    return redirect('cart:detail')


@require_POST
def cart_update(request, product_id):
    """Оновлення кількості товару в кошику"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    try:
        data = json.loads(request.body) if request.body else {}
        quantity = int(data.get('quantity', request.POST.get('quantity', 1)))
    except (json.JSONDecodeError, ValueError, KeyError):
        quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart.add(product=product, quantity=quantity, override_quantity=True)
        message = 'Кількість оновлено'
        success = True
    else:
        cart.remove(product)
        message = 'Товар видалено з кошика'
        success = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': success,
            'message': message,
            'cart_count': len(cart),
            'subtotal': str(cart.get_subtotal()),
            'total': str(cart.get_total_price())
        })
    
    return redirect('cart:detail')


@require_POST
def apply_promo_code(request):
    """Застосування промокоду"""
    cart = Cart(request)
    
    try:
        data = json.loads(request.body) if request.body else {}
        code = data.get('code', request.POST.get('code', '')).strip()
    except (json.JSONDecodeError, AttributeError):
        code = request.POST.get('code', '').strip()
    
    if not code:
        return JsonResponse({
            'success': False,
            'message': 'Введіть промокод'
        })
    
    success, message = cart.apply_promo_code(code)
    
    return JsonResponse({
        'success': success,
        'message': message,
        'promo_code': cart.promo_code if success else None,
        'promo_discount': str(cart.get_promo_discount()) if success else '0',
        'total': str(cart.get_total_price())
    })


@require_POST
def remove_promo_code(request):
    """Видалення промокоду"""
    cart = Cart(request)
    cart.remove_promo_code()
    
    return JsonResponse({
        'success': True,
        'message': 'Промокод видалено',
        'total': str(cart.get_total_price())
    })


@require_POST
def clear_cart(request):
    """Очищення кошика"""
    cart = Cart(request)
    cart.clear()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'message': 'Кошик очищено'
        })
    
    return redirect('cart:detail')
