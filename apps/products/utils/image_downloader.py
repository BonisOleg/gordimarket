"""
Утиліта для завантаження зображень товарів
"""
from apps.products.models import ProductImage


def download_product_images(product, picture_urls, clear_existing=True, use_urls=True):
    """
    Додає зображення для товару
    
    Args:
        product: Product instance
        picture_urls: список URL зображень
        clear_existing: чи видаляти існуючі зображення
        use_urls: зберігати URL замість завантаження файлів
    
    Returns:
        tuple: (успішно_додано, помилок)
    """
    if not picture_urls:
        return 0, 0
    
    if clear_existing:
        product.images.all().delete()
    
    success = 0
    errors = 0
    
    for idx, picture_url in enumerate(picture_urls):
        if not picture_url:
            continue
            
        try:
            ProductImage.objects.create(
                product=product,
                image_url=picture_url,
                is_main=(idx == 0),
                sort_order=idx,
            )
            success += 1
        except Exception:
            errors += 1
    
    return success, errors

