from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Min, Max
from django.db.models.functions import Lower
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from collections import OrderedDict
import logging
from .models import Product, Category, ProductAttribute

logger = logging.getLogger(__name__)


def _category_base_qs(category, child_ids):
    """Unfiltered queryset scoped to a category and its children."""
    qs = Product.objects.filter(is_active=True)
    if child_ids:
        qs = qs.filter(
            Q(categories__id=category.id) |
            Q(primary_category__id=category.id) |
            Q(categories__id__in=child_ids) |
            Q(primary_category__id__in=child_ids)
        ).distinct()
    else:
        qs = qs.filter(
            Q(categories__id=category.id) | Q(primary_category__id=category.id)
        ).distinct()
    return qs


class CategoryView(ListView):
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        from .models import ProductImage

        self.category = get_object_or_404(
            Category.objects.select_related('parent').prefetch_related(
                Prefetch('children', queryset=Category.objects.filter(is_active=True).order_by('sort_order', 'name'))
            ),
            slug=self.kwargs['slug']
        )

        child_categories = list(self.category.children.all())
        self._child_categories = child_categories
        child_ids = [c.id for c in child_categories]

        base_qs = Product.objects.select_related('primary_category').prefetch_related(
            'categories',
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_main=True).only(
                    'image', 'image_url', 'is_main', 'product_id'
                ),
                to_attr='main_images'
            )
        ).filter(is_active=True)

        if child_ids:
            base_qs = base_qs.filter(
                Q(categories__id=self.category.id) |
                Q(primary_category__id=self.category.id) |
                Q(categories__id__in=child_ids) |
                Q(primary_category__id__in=child_ids)
            ).distinct()
        else:
            base_qs = base_qs.filter(
                Q(categories__id=self.category.id) | Q(primary_category__id=self.category.id)
            ).distinct()

        params = self.request.GET

        # Subcategory filter
        selected_subcats = params.getlist('subcategory')
        if selected_subcats and child_ids:
            subcat_ids = list(
                Category.objects.filter(
                    slug__in=selected_subcats, id__in=child_ids
                ).values_list('id', flat=True)
            )
            if subcat_ids:
                base_qs = base_qs.filter(
                    Q(categories__id__in=subcat_ids) | Q(primary_category__id__in=subcat_ids)
                )

        # In-stock filter
        if params.get('in_stock') == '1':
            base_qs = base_qs.filter(stock__gt=0)

        # Brand filter (case-insensitive)
        brands = params.getlist('brand')
        if brands:
            brand_q = Q()
            for b in brands:
                brand_q |= Q(brand__iexact=b)
            base_qs = base_qs.filter(brand_q)

        # Price range
        try:
            price_min = int(params.get('price_min', 0))
            if price_min > 0:
                base_qs = base_qs.filter(retail_price__gte=price_min)
        except (ValueError, TypeError):
            price_min = 0

        try:
            price_max = int(params.get('price_max', 0))
            if price_max > 0:
                base_qs = base_qs.filter(retail_price__lte=price_max)
        except (ValueError, TypeError):
            price_max = 0

        # Dynamic attribute filters (attr_<name>=<value>)
        for key in params:
            if key.startswith('attr_'):
                attr_name = key[5:]
                attr_values = params.getlist(key)
                if attr_values:
                    base_qs = base_qs.filter(
                        attributes__name=attr_name,
                        attributes__value__in=attr_values
                    )

        # Sorting
        sort = params.get('sort', 'default')
        sort_map = {
            'price_asc': 'retail_price',
            'price_desc': '-retail_price',
            'name_asc': 'name',
            'name_desc': '-name',
            'new': '-created_at',
            'popular': '-is_top',
        }
        order = sort_map.get(sort, '-created_at')
        base_qs = base_qs.order_by(order)

        self._child_ids = [c.id for c in child_categories]
        return base_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category

        child_categories = self._child_categories
        context['subcategories'] = child_categories
        context['available_subcategories'] = child_categories

        params = self.request.GET
        child_ids = self._child_ids

        all_cat_qs = _category_base_qs(self.category, child_ids)

        # Brands (deduplicated case-insensitively)
        raw_brands = all_cat_qs.exclude(brand='').values_list('brand', flat=True).distinct()
        seen_brands = {}
        for b in raw_brands:
            key = b.strip().lower()
            if key and key not in seen_brands:
                seen_brands[key] = b.strip()
        available_brands = sorted(seen_brands.values(), key=lambda x: x.lower())
        context['available_brands'] = available_brands

        # Price range
        price_agg = all_cat_qs.aggregate(mn=Min('retail_price'), mx=Max('retail_price'))
        context['cat_min_price'] = int(price_agg['mn'] or 0)
        context['cat_max_price'] = int(price_agg['mx'] or 10000)

        # Dynamic attributes available in this category
        attr_qs = ProductAttribute.objects.filter(
            product__in=all_cat_qs
        ).values_list('name', 'value').distinct().order_by('name', 'value')

        available_attributes = OrderedDict()
        for name, value in attr_qs:
            available_attributes.setdefault(name, []).append(value)
        context['available_attributes'] = available_attributes

        # Current filter state for template
        try:
            context['filter_price_min'] = int(params.get('price_min', 0))
        except (ValueError, TypeError):
            context['filter_price_min'] = 0
        try:
            context['filter_price_max'] = int(params.get('price_max', 0))
        except (ValueError, TypeError):
            context['filter_price_max'] = 0

        context['filter_brands'] = params.getlist('brand')
        context['filter_in_stock'] = params.get('in_stock') == '1'
        context['current_sort'] = params.get('sort', 'default')
        context['filter_subcategories'] = params.getlist('subcategory')

        # Collect selected attribute filters
        filter_attrs = {}
        for key in params:
            if key.startswith('attr_'):
                filter_attrs[key] = params.getlist(key)
        context['filter_attrs'] = filter_attrs

        # Build query string without page param for pagination links
        qs_copy = params.copy()
        qs_copy.pop('page', None)
        context['filter_querystring'] = qs_copy.urlencode()

        return context


class ProductDetailView(DetailView):
    """Детальна сторінка товару"""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        from .models import ProductImage
        return Product.objects.filter(is_active=True, stock__gt=0).prefetch_related(
            Prefetch('images',
                queryset=ProductImage.objects.only('image', 'image_url', 'is_main', 'alt_text', 'product_id').order_by('sort_order', 'id')
            )
        )


@method_decorator(cache_page(60 * 1), name='dispatch')
class SaleProductsView(ListView):
    """Акції - показує товари з активними акціями"""
    model = Product
    template_name = 'products/sale.html'
    context_object_name = 'products'
    paginate_by = 15
    
    def get_queryset(self):
        from django.utils import timezone
        from .models import ProductImage
        
        now = timezone.now()
        
        return Product.objects.filter(
            is_sale=True,
            sale_price__isnull=False,
            is_active=True,
            stock__gt=0
        ).filter(
            Q(sale_start_date__isnull=True) | Q(sale_start_date__lte=now)
        ).filter(
            Q(sale_end_date__isnull=True) | Q(sale_end_date__gt=now)
        ).select_related('primary_category').prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_main=True).only('image', 'image_url', 'is_main', 'product_id'),
                to_attr='main_images'
            )
        ).only(
            'id', 'name', 'slug', 'retail_price', 'sale_price', 'is_sale',
            'sale_start_date', 'sale_end_date', 'primary_category__name', 'stock'
        ).order_by('-updated_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # total_products видалено - не використовується в template
        return context


@csrf_exempt
@require_POST
def trigger_sync(request):
    """Endpoint для тригеру синхронізації (для cron-job.org)"""
    secret = request.POST.get('secret', '')
    
    if secret != getattr(settings, 'CRON_SECRET', 'change-me'):
        logger.warning(f'Unauthorized cron attempt from {request.META.get("REMOTE_ADDR")}')
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        logger.info('Starting sync from cron trigger')
        call_command('sync_products', '--skip-images')
        call_command('update_prices_xls')
        logger.info('Sync completed successfully')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f'Sync error: {e}', exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
