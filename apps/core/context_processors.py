from apps.products.models import Category
from apps.cart.cart import Cart
from apps.wishlist.wishlist import Wishlist
from django.db.models import Prefetch
from django.core.cache import cache


def _get_site_settings():
    """Return cached SiteSettings singleton."""
    ss = cache.get('site_settings_obj')
    if ss is None:
        from apps.core.models import SiteSettings
        ss = SiteSettings.objects.first()
        cache.set('site_settings_obj', ss, 3600)
    return ss


def base_context(request):
    main_categories = cache.get('main_categories_menu')

    if main_categories is None:
        children_queryset = Category.objects.filter(
            is_active=True,
            parent__isnull=False
        ).select_related('parent').only(
            'id', 'name', 'slug', 'parent_id', 'sort_order', 'icon'
        ).order_by('sort_order', 'name')

        main_categories = list(Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related(
            Prefetch('children', queryset=children_queryset)
        ).only('id', 'name', 'slug', 'sort_order', 'icon').order_by('sort_order', 'name'))

        cache.set('main_categories_menu', main_categories, 3600)

    ss = _get_site_settings()

    context = {
        'main_categories': main_categories,
        'site_settings_obj': ss,
        # Convenience shortcuts used across templates
        'site_name': ss.site_name if ss else 'Shop',
        'site_tagline': ss.site_tagline if ss else '',
        'site_description': ss.site_description if ss else '',
        'site_keywords': ss.site_keywords if ss else '',
        'site_phone': ss.phone if ss else '',
        'site_phone_raw': ss.phone_raw if ss else '',
        'site_email': ss.email if ss else '',
        'site_address': ss.address if ss else '',
        'site_working_hours': ss.working_hours if ss else '',
        'site_day_off': ss.day_off if ss else '',
        'site_search_placeholder': ss.search_placeholder if ss else 'Пошук товарів...',
        'site_viber': ss.viber_number if ss else '',
        'site_telegram': ss.telegram_link if ss else '',
        'site_whatsapp': ss.whatsapp_number if ss else '',
        'site_instagram': ss.instagram_url if ss else '',
        'site_facebook': ss.facebook_url if ss else '',
        'site_theme_color': ss.theme_color if ss else '#4A90D9',
        'site_copyright': ss.get_copyright() if ss else 'My Shop',
        'site_age_verification': ss.age_verification_enabled if ss else False,
    }

    if hasattr(request, 'session'):
        cart = Cart(request)
        context['cart'] = cart
        context['cart_total_items'] = len(cart)
        context['cart_total_price'] = cart.get_total_price()

        wishlist = Wishlist(request)
        context['wishlist_count'] = len(wishlist)

    return context
