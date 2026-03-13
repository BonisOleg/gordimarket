from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('sale/', views.SaleProductsView.as_view(), name='sale'),
    path('api/trigger-sync/', views.trigger_sync, name='trigger_sync'),
]
