from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from shakespeare_setup.config import get_all_configs


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class SetUpOverview(AccessabilityMixin, TemplateView):
    template_name = "setup/overview.html"

    def get_context_data(self, **kwargs):
        context = super(SetUpOverview, self).get_context_data(**kwargs)

        context['setup_configs'] = get_all_configs(request=self.request)


        return context
