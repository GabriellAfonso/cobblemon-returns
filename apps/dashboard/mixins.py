from django.contrib.auth.mixins import AccessMixin


class StaffRequiredMixin(AccessMixin):
    """Redirect to admin login if user is not authenticated or not staff."""
    login_url = '/admin/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
