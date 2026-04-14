from django.urls import path

from .views import WikiDetailView, WikiListView

urlpatterns = [
    path('', WikiListView.as_view(), name='wiki-list'),
    path('<slug:slug>/', WikiDetailView.as_view(), name='wiki-detail'),
]
