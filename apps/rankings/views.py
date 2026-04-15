from django.views.generic import TemplateView

from apps.players.repositories.stats_repository import PlayerStatsRepository
from apps.rankings.services.ranking_service import RankingService


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = RankingService(PlayerStatsRepository())
        ctx['leaders'] = service.get_home_leaders()
        return ctx


class RankingsView(TemplateView):
    template_name = 'rankings/page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = RankingService(PlayerStatsRepository())
        ctx['rankings'], ctx['last_updated'] = service.get_full_rankings()
        return ctx
