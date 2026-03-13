"""
Context processors для wishlist
"""
from .wishlist import Wishlist


def wishlist(request):
    """Додає wishlist в контекст всіх шаблонів"""
    wl = Wishlist(request)
    return {
        'wishlist': wl,
        'wishlist_count': len(wl)
    }

