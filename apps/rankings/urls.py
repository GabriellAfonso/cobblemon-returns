from django.urls import path

from .views import HomeView, RankingsView

app_name = 'rankings'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('rankings/', RankingsView.as_view(), name='rankings'),
]
