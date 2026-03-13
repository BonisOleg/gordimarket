"""
Custom template filters для products
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Отримує елемент зі словника за ключем"""
    if dictionary:
        return dictionary.get(key)
    return None


@register.filter
def get_attribute(product, attr_name):
    """Отримує значення атрибута товару"""
    attr = product.attributes.filter(name=attr_name).first()
    return attr.value if attr else ''

