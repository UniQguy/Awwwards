"""
URL routes for full-text search and autosuggestions.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.search_view, name="search_results"),
    path("suggest/", views.search_suggest, name="search_suggest"),
]
