from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse_lazy


class StaffRequiredMixin(AccessMixin):
    login_url = reverse_lazy("admin:login")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.get_login_url())
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
