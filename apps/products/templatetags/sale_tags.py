"""
Template tags для роботи з акціями
"""
from django import template
from django.utils import timezone

register = template.Library()


@register.simple_tag
def get_sale_end_timestamp(product):
    """Повертає timestamp завершення акції для таймера"""
    if product.sale_end_date:
        return int(product.sale_end_date.timestamp() * 1000)
    return None


@register.filter
def time_until_end(end_date):
    """Повертає час до завершення у читабельному форматі"""
    if not end_date:
        return ""
    
    now = timezone.now()
    if end_date <= now:
        return "Завершено"
    
    delta = end_date - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days} дн. {hours} год."
    elif hours > 0:
        return f"{hours} год. {minutes} хв."
    else:
        return f"{minutes} хв."

