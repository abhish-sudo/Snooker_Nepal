from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='list'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='detail'),
    path('brand/<slug:slug>/', views.BrandView.as_view(), name='brand'),
]