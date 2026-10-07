"""
URL routes for catalog browsing, categorization, products, and comparison.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("categories/", views.category_list, name="category_list"),
    path("c/<slug:slug>/count/", views.category_price_count, name="category_price_count"),
    path("c/<slug:slug>/", views.category_detail, name="category_detail"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("brands/", views.brand_list, name="brand_list"),
    path("compare/", views.compare_tray, name="compare_tray"),
    path("compare/add/<int:product_id>/", views.compare_add, name="compare_add"),
    path("compare/remove/<int:product_id>/", views.compare_remove, name="compare_remove"),
    path("compare/clear/", views.compare_clear, name="compare_clear"),
]
