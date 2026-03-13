"""
Core Views - основні представлення сайту
"""
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Prefetch
from django.db.models.functions import Lower
from django.db import connection
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from apps.products.models import Product, Category, ProductReview
from .models import Banner

# PostgreSQL Full-Text Search (якщо доступний)
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


def healthcheck(request):
    """Простий healthcheck endpoint для Render"""
    return HttpResponse("OK", status=200)


@method_decorator(cache_page(60 * 10), name='dispatch')
class HomeView(TemplateView):
    """Головна сторінка"""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Отримуємо активні банери
        banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')
        
        # Отримуємо акційні товари (тільки з АКТИВНИМИ акціями)
        from django.utils import timezone
        now = timezone.now()
        
        from apps.products.models import ProductImage
        
        sale_products = Product.objects.filter(
            is_active=True,
            is_sale=True,
            sale_price__isnull=False,
            stock__gt=0
        ).filter(
            Q(sale_start_date__isnull=True) | Q(sale_start_date__lte=now)
        ).filter(
            Q(sale_end_date__isnull=True) | Q(sale_end_date__gt=now)
        ).select_related('primary_category').prefetch_related(
            Prefetch('images',
                queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main', 'product_id'),
                to_attr='main_images'
            )
        ).order_by('sort_order', '-created_at')[:8]
        
        from apps.products.models import TopProduct
        top_product_entries = TopProduct.objects.filter(
            is_active=True,
            product__is_active=True,
            product__stock__gt=0
        ).select_related('product__primary_category').prefetch_related(
            Prefetch('product__images',
                queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main', 'product_id'),
                to_attr='main_images'
            )
        ).order_by('sort_order', '-created_at')[:8]
        
        top_products = [entry.product for entry in top_product_entries]
        
        # Отримуємо схвалені відгуки
        reviews = ProductReview.objects.filter(
            is_approved=True
        ).select_related('product').prefetch_related(
            Prefetch('product__images',
                queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main', 'product_id'),
                to_attr='main_images'
            )
        ).order_by('-created_at')[:6]
        
        context.update({
            'banners': banners,
            'sale_products': sale_products,
            'top_products': top_products,
            'reviews': reviews,
        })
        return context


class DeliveryView(TemplateView):
    """Доставка та оплата"""
    template_name = 'core/delivery.html'


class ReturnsView(TemplateView):
    """Повернення та обмін"""
    template_name = 'core/returns.html'


class AboutView(TemplateView):
    """Про нас"""
    template_name = 'core/about.html'


class ContactsView(TemplateView):
    """Контакти"""
    template_name = 'core/contacts.html'


class TermsView(TemplateView):
    """Умови використання"""
    template_name = 'core/terms.html'


class PrivacyView(TemplateView):
    """Політика конфіденційності"""
    template_name = 'core/privacy.html'


def _get_trigram_threshold(query: str) -> float:
    """Dynamic threshold: shorter queries need lower threshold to match."""
    length = len(query)
    if length <= 3:
        return 0.1
    if length <= 5:
        return 0.15
    return 0.25


def _search_annotations():
    """Lower-cased field annotations for case-insensitive search on any DB."""
    return dict(
        _name_l=Lower('name'),
        _brand_l=Lower('brand'),
        _sku_l=Lower('sku'),
        _vendor_l=Lower('vendor_name'),
        _cat_l=Lower('primary_category__name'),
    )


def _build_search_q(q_lower: str):
    """Q filter across lowered annotations. Caller must .annotate(**_search_annotations()) first."""
    return (
        Q(_name_l__contains=q_lower) |
        Q(_brand_l__contains=q_lower) |
        Q(_sku_l__contains=q_lower) |
        Q(_vendor_l__contains=q_lower) |
        Q(_cat_l__contains=q_lower)
    )


class SearchView(TemplateView):
    """Пошук товарів - оптимізований з кешуванням"""
    template_name = 'core/search.html'

    def get_context_data(self, **kwargs):
        from django.core.cache import cache

        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()

        if query:
            cache_key = f'search_initial:{query.lower()}'
            cached_data = cache.get(cache_key)

            if cached_data:
                context.update(cached_data)
            else:
                db_engine = connection.settings_dict['ENGINE']
                use_postgres = 'postgresql' in db_engine and POSTGRES_AVAILABLE
                threshold = _get_trigram_threshold(query)

                q_lower = query.lower()

                if use_postgres:
                    from django.contrib.postgres.search import TrigramSimilarity

                    products = Product.objects.filter(
                        is_active=True,
                        stock__gt=0
                    ).annotate(
                        **_search_annotations(),
                        similarity=TrigramSimilarity('_name_l', q_lower),
                    ).filter(
                        _build_search_q(q_lower) | Q(similarity__gt=threshold)
                    ).order_by('-similarity', 'name').select_related('primary_category').only(
                        'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                        'sale_start_date', 'sale_end_date', 'is_top', 'is_new',
                        'brand', 'vendor_name',
                        'primary_category__name', 'primary_category__slug'
                    ).distinct()[:20]
                else:
                    products = Product.objects.filter(
                        is_active=True,
                        stock__gt=0
                    ).annotate(
                        **_search_annotations(),
                    ).filter(
                        _build_search_q(q_lower)
                    ).select_related('primary_category').only(
                        'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                        'sale_start_date', 'sale_end_date', 'is_top', 'is_new',
                        'brand', 'vendor_name',
                        'primary_category__name', 'primary_category__slug'
                    ).order_by('name').distinct()[:20]

                data = {
                    'products': products,
                    'query': query,
                    'initial_count': len(products),
                }
                cache.set(cache_key, data, 300)
                context.update(data)

        return context


def search_autocomplete(request):
    """API для автокомпліту пошуку - швидкий з низьким порогом тригам"""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    try:
        from apps.products.models import ProductImage

        db_engine = connection.settings_dict['ENGINE']
        use_postgres_search = 'postgresql' in db_engine and POSTGRES_AVAILABLE
        threshold = _get_trigram_threshold(query)
        q_lower = query.lower()

        if use_postgres_search:
            from django.contrib.postgres.search import TrigramSimilarity

            products = Product.objects.filter(
                is_active=True,
                stock__gt=0
            ).annotate(
                **_search_annotations(),
                similarity=TrigramSimilarity('_name_l', q_lower),
            ).filter(
                _build_search_q(q_lower) | Q(similarity__gt=threshold)
            ).order_by('-similarity', 'name').select_related('primary_category').prefetch_related(
                Prefetch('images',
                    queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main'),
                    to_attr='main_images'
                )
            ).only(
                'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                'sale_start_date', 'sale_end_date', 'brand', 'vendor_name',
                'primary_category__name', 'primary_category__slug'
            )[:8]
        else:
            products = Product.objects.filter(
                is_active=True,
                stock__gt=0
            ).annotate(
                **_search_annotations(),
            ).filter(
                _build_search_q(q_lower)
            ).select_related('primary_category').prefetch_related(
                Prefetch('images',
                    queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main'),
                    to_attr='main_images'
                )
            ).only(
                'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                'sale_start_date', 'sale_end_date', 'brand', 'vendor_name',
                'primary_category__name', 'primary_category__slug'
            ).order_by('name')[:8]

        results = []
        for p in products:
            image_url = None
            if hasattr(p, 'main_images') and p.main_images:
                img = p.main_images[0]
                image_url = img.image_url if img.image_url else (img.image.url if img.image else None)

            price = p.sale_price if (p.is_sale and p.sale_price) else p.retail_price
            category_name = p.primary_category.name if p.primary_category else ''

            results.append({
                'name': p.name,
                'url': p.get_absolute_url(),
                'price': str(int(price)),
                'image': image_url,
                'category': category_name,
            })

        return JsonResponse({'results': results})
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Search autocomplete error: {e}')
        return JsonResponse({'results': [], 'error': str(e)}, status=500)


def search_paginated(request):
    """API для пагінованого пошуку - оптимізований з кешуванням"""
    from django.core.cache import cache

    query = request.GET.get('q', '').strip()
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))

    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)

    cache_key = f'search:{query.lower()}:page{page}:per{per_page}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return JsonResponse(cached_result)

    try:
        db_engine = connection.settings_dict['ENGINE']
        use_postgres_search = 'postgresql' in db_engine and POSTGRES_AVAILABLE
        threshold = _get_trigram_threshold(query)
        q_lower = query.lower()

        if use_postgres_search:
            from django.contrib.postgres.search import TrigramSimilarity

            base_queryset = Product.objects.filter(
                is_active=True,
                stock__gt=0
            ).annotate(
                **_search_annotations(),
                similarity=TrigramSimilarity('_name_l', q_lower),
            ).filter(
                _build_search_q(q_lower) | Q(similarity__gt=threshold)
            ).order_by('-similarity', 'name').select_related('primary_category').only(
                'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                'sale_start_date', 'sale_end_date', 'is_top', 'is_new',
                'brand', 'vendor_name',
                'primary_category__name', 'primary_category__slug'
            ).distinct()
        else:
            base_queryset = Product.objects.filter(
                is_active=True,
                stock__gt=0
            ).annotate(
                **_search_annotations(),
            ).filter(
                _build_search_q(q_lower)
            ).select_related('primary_category').only(
                'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
                'sale_start_date', 'sale_end_date', 'is_top', 'is_new',
                'brand', 'vendor_name',
                'primary_category__name', 'primary_category__slug'
            ).order_by('name').distinct()

        count_cache_key = f'search_count:{query.lower()}'
        total_count = cache.get(count_cache_key)
        if total_count is None:
            total_count = base_queryset.count()
            cache.set(count_cache_key, total_count, 300)

        offset = (page - 1) * per_page
        products = base_queryset[offset:offset + per_page]

        results = []
        for p in products:
            image_url = None
            try:
                main_image = p.images.filter(is_main=True).only('image', 'image_url').first()
                if not main_image:
                    main_image = p.images.only('image', 'image_url').first()
                if main_image:
                    image_url = main_image.image_url if main_image.image_url else (main_image.image.url if main_image.image else None)
            except Exception:
                pass

            is_in_stock = p.is_in_stock() if hasattr(p, 'is_in_stock') else True

            sale_end_timestamp = None
            if p.is_sale_active() and p.sale_end_date:
                from django.utils import timezone
                sale_end_timestamp = int(p.sale_end_date.timestamp() * 1000)

            results.append({
                'id': p.id,
                'name': p.name,
                'url': p.get_absolute_url(),
                'retail_price': str(int(p.retail_price)) if p.retail_price else '0',
                'sale_price': str(int(p.sale_price)) if p.sale_price else None,
                'image': image_url,
                'category': p.primary_category.name if p.primary_category else '',
                'is_sale': p.is_sale_active(),
                'is_top': p.is_top,
                'is_new': p.is_new,
                'is_in_stock': is_in_stock,
                'sale_end_timestamp': sale_end_timestamp,
            })

        total_pages = (total_count + per_page - 1) // per_page

        response_data = {
            'products': results,
            'total_count': total_count,
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }

        cache.set(cache_key, response_data, 300)
        return JsonResponse(response_data)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Search paginated error: {e}')
        return JsonResponse({'error': str(e)}, status=500)
