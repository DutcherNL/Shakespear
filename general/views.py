from django.views.generic import TemplateView, ListView, FormView, View
from django.contrib.auth import views as account_views
from django.urls import reverse, reverse_lazy


class LogInView(account_views.LoginView):
    template_name = "accounts/login.html"


class LogOutView(account_views.LogoutView):
    pass


class StepDisplayMixin:
    """ Adds a display for step progress """
    step = None
    enable_step_2 = False
    enable_step_3 = False

    def __init__(self, *args, **kwargs):
        assert self.step is not None
        super(StepDisplayMixin, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StepDisplayMixin, self).get_context_data(**kwargs)
        context['progress_step'] = self.step
        context['enable_step_2'] = self.enable_step_2 or self.step >= 2
        context['enable_step_3'] = self.enable_step_3 or self.step >= 3
        return context