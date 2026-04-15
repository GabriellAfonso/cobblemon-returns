from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect


class StaffRequiredMixin(AccessMixin):
    """Redirect to admin login if user is not authenticated or not staff."""
    login_url = '/admin/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)
