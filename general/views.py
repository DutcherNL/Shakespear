from django.views.generic import TemplateView, ListView, FormView, View
from django.contrib.auth import views as account_views
from django.urls import reverse, reverse_lazy



class LogInView(account_views.LoginView):
    template_name = "accounts/login.html"


class LogOutView(account_views.LogoutView):
    pass