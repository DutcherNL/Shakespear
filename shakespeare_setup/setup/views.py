from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class SetUpOverview(AccessabilityMixin, TemplateView):
    template_name = "inquiry/setup/overview.html"