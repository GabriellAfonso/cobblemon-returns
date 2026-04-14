from django.views.generic import TemplateView

from apps.players.models import PlayerStats

from .config import RANKINGS
from .formatters import format_value


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        leaders = []
        for r in RANKINGS:
            top = (
                PlayerStats.objects.order_by(f'-{r["field"]}')
                .select_related('player')
                .first()
            )
            if top:
                leaders.append({
                    'id': r['id'],
                    'label': r['label'],
                    'icon': r['icon'],
                    'player_name': top.player.username,
                    'value': format_value(getattr(top, r['field']), r['format']),
                })
        ctx['leaders'] = leaders
        return ctx


class RankingsView(TemplateView):
    template_name = 'rankings/page.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rankings = []
        for r in RANKINGS:
            top10 = list(
                PlayerStats.objects.order_by(f'-{r["field"]}')
                .select_related('player')[:10]
            )
            max_val = getattr(top10[0], r['field']) if top10 else 1
            players = []
            for stat in top10:
                raw = getattr(stat, r['field'])
                players.append({
                    'name': stat.player.username,
                    'raw_value': raw,
                    'value': format_value(raw, r['format']),
                    'bar_pct': round((raw / max_val) * 100) if max_val else 0,
                })
            rankings.append({**r, 'players': players})

        last_updated = (
            PlayerStats.objects.order_by('-updated_at')
            .values_list('updated_at', flat=True)
            .first()
        )
        ctx['rankings'] = rankings
        ctx['last_updated'] = last_updated
        return ctx
