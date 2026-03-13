"""
Core URLs - основні сторінки сайту
"""
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('delivery/', views.DeliveryView.as_view(), name='delivery'),
    path('returns/', views.ReturnsView.as_view(), name='returns'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('contacts/', views.ContactsView.as_view(), name='contacts'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('healthz/', views.healthcheck, name='healthcheck'),
    
    # Нові юридичні сторінки
    path('terms/', views.TermsView.as_view(), name='terms'),
    path('privacy/', views.PrivacyView.as_view(), name='privacy'),
    
    # API для пошуку
    path('api/search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('api/search/paginated/', views.search_paginated, name='search_paginated'),
]
