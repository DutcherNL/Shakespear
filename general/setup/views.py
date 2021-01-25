from django.views.generic import ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

from general.models import BasePageURL


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class GeneralPageListView(AccessabilityMixin, ListView):
    template_name = "general/setup/general_page_overview.html"
    context_object_name = "pages"
    model = BasePageURL


class AddGeneralPageView(AccessabilityMixin, CreateView):
    model = BasePageURL
    success_url = reverse_lazy('setup:general:list')
    template_name = "general/setup/general_page_add.html"
    fields = ['name', 'slug', 'description', 'in_footer', 'footer_order']


class UpdateGeneralPageView(AccessabilityMixin, UpdateView):
    template_name = "general/setup/general_page_update.html"
    pk_url_kwarg = "tech_id"
    model = BasePageURL
    fields = ['name', 'slug', 'description', 'in_footer', 'footer_order']

    def get_context_data(self, **kwargs):
        context = super(UpdateGeneralPageView, self).get_context_data(**kwargs)
        context['breadcrumb_name'] = f"Edit {self.object.name}"
        context['breadcrumb_url_name'] = "create_page"
        return context

    def get_success_url(self):
        return reverse('setup:general:list')


class DeleteGeneralPageView(DeleteView):
    model = BasePageURL
    success_url = reverse_lazy('setup:general:list')
    template_name = "general/setup/general_page_delete.html"
