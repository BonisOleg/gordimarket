"""
Sitemaps для SEO оптимізації
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap для статичних сторінок"""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'core:home',
            'core:delivery',
            'core:returns',
            'core:about',
            'core:contacts',
        ]

    def location(self, item):
        return reverse(item)
