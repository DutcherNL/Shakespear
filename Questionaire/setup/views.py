from django.views.generic import TemplateView, ListView, FormView
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse

from Questionaire.models import Technology
from Questionaire.widgets import IconInput
from Questionaire.setup.forms import CreatePageForTechForm


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class SetUpOverview(AccessabilityMixin, TemplateView):
    template_name = "inquiry/setup/overview.html"


class SetUpTechPageOverview(AccessabilityMixin, ListView):
    template_name = "inquiry/setup/tech_overview.html"
    context_object_name = "technologies"
    model = Technology


class UpdateTechnologyView(AccessabilityMixin, UpdateView):
    template_name = "inquiry/setup/tech_update.html"
    pk_url_kwarg = "tech_id"
    model = Technology
    fields = ['name', 'short_text', 'icon']

    def get_form(self, form_class=None):
        form = super(UpdateTechnologyView, self).get_form(form_class=form_class)
        form.fields['icon'].widget = IconInput()
        return form

    def get_context_data(self, **kwargs):
        context = super(UpdateTechnologyView, self).get_context_data(**kwargs)
        context['breadcrumb_name'] = f"Edit {self.object}"
        context['breadcrumb_url_name'] = "create_page"
        return context


class TechnologyMixin:
    def dispatch(self, request, *args, **kwargs):
        self.technology = get_object_or_404(Technology, id=self.kwargs['tech_id'])
        return super(TechnologyMixin, self).dispatch(request, *args, *kwargs)


class CreateTechPageView(AccessabilityMixin, TechnologyMixin, FormView):
    template_name = "inquiry/setup/create_tech_page.html"
    form_class = CreatePageForTechForm

    def get_form_kwargs(self):
        form_kwargs = super(CreateTechPageView, self).get_form_kwargs()
        form_kwargs['initial'] = {'technology': self.technology}
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super(CreateTechPageView, self).get_context_data(**kwargs)
        context['breadcrumb_name'] = "Add technology"
        context['breadcrumb_url_name'] = "create_page"
        return context

    def form_valid(self, form):
        form.save()
        return super(CreateTechPageView, self).form_valid(form)

    def get_success_url(self):
        return reverse('setup:pages:edit_page',
                       kwargs={'tech_id': self.technology.id},
                       current_app=self.request.resolver_match.namespace)

