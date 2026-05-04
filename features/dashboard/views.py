import mistune
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from features.collector.repositories.log_repository import CollectionLogRepository
from features.dashboard.services.dashboard_service import DashboardService
from features.players.repositories.player_repository import PlayerRepository
from features.wiki.models import WikiPage

from .forms import WikiPageForm
from .mixins import StaffRequiredMixin

_VALID_SORT_FIELDS = {
    "play_time_ticks",
    "pokemons_caught",
    "pokedex_registered",
    "cobbletcg_cards",
    "battles_won",
    "cobbledollars",
}


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        service = DashboardService(PlayerRepository(), CollectionLogRepository())
        ctx.update(service.get_summary())

        next_run = None
        try:
            from features.collector.tasks import scheduler

            job = scheduler.get_job("collect")
            if job:
                next_run = job.next_run_time
        except Exception:
            pass
        ctx["next_run"] = next_run
        return ctx


class WikiManageView(StaffRequiredMixin, ListView):
    model = WikiPage
    template_name = "dashboard/wiki_list.html"
    context_object_name = "pages"
    paginate_by = 20


class WikiCreateView(StaffRequiredMixin, CreateView):
    model = WikiPage
    form_class = WikiPageForm
    template_name = "dashboard/wiki_form.html"
    success_url = reverse_lazy("dashboard:wiki-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        content = self.request.POST.get("content", "")
        ctx["preview_html"] = mistune.html(content) if content else ""
        ctx["form_title"] = "New Wiki Page"
        return ctx


class WikiEditView(StaffRequiredMixin, UpdateView):
    model = WikiPage
    form_class = WikiPageForm
    template_name = "dashboard/wiki_form.html"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("dashboard:wiki-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        content = self.request.POST.get("content", self.object.content)
        ctx["preview_html"] = mistune.html(content)
        ctx["form_title"] = f"Edit: {self.object.title}"
        return ctx


class WikiDeleteView(StaffRequiredMixin, DeleteView):
    model = WikiPage
    template_name = "dashboard/wiki_confirm_delete.html"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("dashboard:wiki-list")


class CollectionLogView(StaffRequiredMixin, ListView):
    template_name = "dashboard/logs.html"
    context_object_name = "logs"

    def get_queryset(self):
        return DashboardService(PlayerRepository(), CollectionLogRepository()).get_logs(
            50
        )


class PlayersListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/players.html"
    context_object_name = "players"

    def get_queryset(self):
        sort = self.request.GET.get("sort", "")
        sort_field = sort if sort in _VALID_SORT_FIELDS else None
        return DashboardService(
            PlayerRepository(), CollectionLogRepository()
        ).get_players(sort_field)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_sort"] = self.request.GET.get("sort", "")
        ctx["sort_fields"] = list(_VALID_SORT_FIELDS)
        return ctx


class TriggerCollectionView(StaffRequiredMixin, View):
    def post(self, request):
        try:
            from features.collector.tasks import run_collection

            run_collection()
            messages.success(request, _("Collection completed successfully."))
        except Exception as e:
            messages.error(request, _("Collection failed: %s") % e)
        return redirect("dashboard:logs")
