from django.views.generic import TemplateView

from features.players.repositories.stats_repository import PlayerStatsRepository
from features.rankings.services.ranking_service import RankingService


class HomeView(TemplateView):
    template_name = "home/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = RankingService(PlayerStatsRepository())
        ctx["leaders"] = service.get_home_leaders()
        return ctx
