"""
Views для списку бажань
"""
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView
from apps.products.models import Product
from .wishlist import Wishlist


class WishlistView(TemplateView):
    """Сторінка списку бажань"""
    template_name = 'wishlist/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist = Wishlist(self.request)
        context['wishlist'] = wishlist
        context['products'] = wishlist.get_products()
        return context


def wishlist_count(request):
    """API для отримання кількості товарів у wishlist"""
    wishlist = Wishlist(request)
    return JsonResponse({'count': len(wishlist)})


@require_POST
def wishlist_add(request, product_id):
    """Додавання товару в список бажань (AJAX)"""
    wishlist = Wishlist(request)
    product = get_object_or_404(Product, id=product_id, is_active=True, stock__gt=0)
    
    added = wishlist.add(product)
    
    return JsonResponse({
        'success': True,
        'added': added,
        'count': len(wishlist),
        'message': 'Товар додано до обраного' if added else 'Товар вже в обраному'
    })


@require_POST
def wishlist_remove(request, product_id):
    """Видалення товару зі списку бажань (AJAX)"""
    wishlist = Wishlist(request)
    product = get_object_or_404(Product, id=product_id)
    
    removed = wishlist.remove(product)
    
    return JsonResponse({
        'success': True,
        'removed': removed,
        'count': len(wishlist),
        'message': 'Товар видалено з обраного'
    })


def wishlist_clear(request):
    """Очищення списку бажань"""
    wishlist = Wishlist(request)
    wishlist.clear()
    return redirect('wishlist:list')

