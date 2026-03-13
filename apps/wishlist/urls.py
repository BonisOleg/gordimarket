"""
URL patterns для wishlist
"""
from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.WishlistView.as_view(), name='list'),
    path('api/count/', views.wishlist_count, name='count'),
    path('add/<int:product_id>/', views.wishlist_add, name='add'),
    path('remove/<int:product_id>/', views.wishlist_remove, name='remove'),
    path('clear/', views.wishlist_clear, name='clear'),
]

