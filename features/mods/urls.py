from django.urls import path

from .views import ModsListView

app_name = "mods"

urlpatterns = [
    path("", ModsListView.as_view(), name="mods-list"),
]
