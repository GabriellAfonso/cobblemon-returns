import mistune
from django.views.generic import DetailView, ListView

from .models import WikiPage


class WikiListView(ListView):
    model = WikiPage
    template_name = 'wiki/list.html'
    context_object_name = 'pages'


class WikiDetailView(DetailView):
    model = WikiPage
    template_name = 'wiki/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['content_html'] = mistune.html(self.object.content)
        return ctx
