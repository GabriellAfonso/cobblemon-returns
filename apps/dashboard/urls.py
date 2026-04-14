from django.urls import path

from .views import (
    CollectionLogView,
    DashboardHomeView,
    PlayersListView,
    TriggerCollectionView,
    WikiCreateView,
    WikiDeleteView,
    WikiEditView,
    WikiManageView,
)

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard-home'),
    path('wiki/', WikiManageView.as_view(), name='dashboard-wiki-list'),
    path('wiki/new/', WikiCreateView.as_view(), name='dashboard-wiki-create'),
    path('wiki/<slug:slug>/edit/', WikiEditView.as_view(), name='dashboard-wiki-edit'),
    path('wiki/<slug:slug>/delete/', WikiDeleteView.as_view(), name='dashboard-wiki-delete'),
    path('logs/', CollectionLogView.as_view(), name='dashboard-logs'),
    path('players/', PlayersListView.as_view(), name='dashboard-players'),
    path('trigger-collection/', TriggerCollectionView.as_view(), name='dashboard-trigger'),
]
