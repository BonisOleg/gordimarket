from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('api/count/', views.cart_count, name='count'),
    path('add/<int:product_id>/', views.cart_add, name='add'),
    path('update/<int:product_id>/', views.cart_update, name='update'),
    path('remove/<int:product_id>/', views.cart_remove, name='remove'),
    path('clear/', views.clear_cart, name='clear'),
    path('promo/apply/', views.apply_promo_code, name='apply_promo'),
    path('promo/remove/', views.remove_promo_code, name='remove_promo'),
]
