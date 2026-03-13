"""
Template tags для Core контенту
"""
from django import template
from apps.core.models import TrackingPixel, SiteSettings

register = template.Library()


@register.simple_tag
def get_site_settings():
    """Отримати глобальні налаштування сайту"""
    return SiteSettings.objects.first()


@register.simple_tag(takes_context=True)
def get_tracking_pixels(context):
    """Отримати активні tracking pixels для поточної сторінки"""
    request = context.get('request')
    if not request:
        # Якщо немає request, повертаємо всі активні
        return TrackingPixel.objects.filter(is_active=True)
    
    # Визначаємо поточну сторінку за URL
    path = request.path.rstrip('/')
    current_page = 'home'
    
    if path == '' or path == '/':
        current_page = 'home'
    elif path == '/delivery':
        current_page = 'delivery'
    elif path == '/returns':
        current_page = 'returns'
    elif path == '/about':
        current_page = 'about'
    elif path == '/contacts':
        current_page = 'contacts'
    elif path == '/terms':
        current_page = 'terms'
    elif path == '/privacy':
        current_page = 'privacy'
    elif path.startswith('/search'):
        current_page = 'search'
    elif path.startswith('/products') and path.count('/') == 2:
        current_page = 'product_list'
    elif path.startswith('/products') and path.count('/') > 2:
        current_page = 'product_detail'
    elif path.startswith('/cart'):
        current_page = 'cart'
    elif path.startswith('/wishlist'):
        current_page = 'wishlist'
    elif path.startswith('/orders'):
        current_page = 'order'
    
    # Отримуємо всі активні піксель
    all_pixels = TrackingPixel.objects.filter(is_active=True)
    
    # Фільтруємо за сторінками
    filtered_pixels = []
    for pixel in all_pixels:
        pages_str = pixel.pages or 'all'
        pages_list = [p.strip() for p in pages_str.split(',')]
        
        # Якщо 'all' або поточна сторінка в списку
        if 'all' in pages_list or current_page in pages_list:
            filtered_pixels.append(pixel)
    
    return filtered_pixels
