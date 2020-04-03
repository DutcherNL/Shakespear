from django.views.generic import TemplateView, ListView, FormView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy

from local_data_storage import models


class AccessabilityMixin(LoginRequiredMixin):
    """ A united mixin that applies for all the reports set-up views
    It is done like this because it makes changing accessiblity (future implementation of permissions) easeier
    """
    pass


class LocalDataStorageOverview(AccessabilityMixin, ListView):
    template_name = "local_data_storage/data_tables_overview.html"
    context_object_name = "datatables"
    model = models.DataTable


class AddLocalDataStorageView(AccessabilityMixin, CreateView):
    model = models.DataTable
    template_name = "local_data_storage/data_table_add.html"
    fields = ['name', 'description']


class DataTableDetailView(AccessabilityMixin, DetailView):
    template_name = "local_data_storage/data_table_info.html"
    slug_url_kwarg = "table_slug"
    model = models.DataTable
    context_object_name = "data_table"


class UpdateLocalDataStorageView(AccessabilityMixin, UpdateView):
    template_name = "local_data_storage/data_table_update.html"
    slug_url_kwarg = "table_slug"
    model = models.DataTable
    fields = ['name', 'description']


class DeleteLocalDataStorageView(AccessabilityMixin, DeleteView):
    model = models.DataTable
    slug_url_kwarg = "table_slug"
    success_url = reverse_lazy('setup:local_data_storage:data_domain_overview')
    template_name = "local_data_storage/data_table_delete.html"


#####################################


class DataTableMixin:
    data_table = None

    def dispatch(self, request, *args, **kwargs):
        self.data_table = get_object_or_404(models.DataTable, slug=kwargs.pop('table_slug'))
        return super(DataTableMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DataTableMixin, self).get_context_data(**kwargs)
        context['data_table'] = self.data_table
        return context

    def get_success_url(self):
        return self.data_table.get_absolute_url()


class AddDataColumnView(AccessabilityMixin, DataTableMixin, CreateView):
    model = models.DataColumn
    template_name = "local_data_storage/data_column_add.html"
    fields = ['name']

    def form_valid(self, form):
        form.instance.table = self.data_table
        return super(AddDataColumnView, self).form_valid(form)


class UpdateDataColumnView(AccessabilityMixin, DataTableMixin, UpdateView):
    template_name = "local_data_storage/data_column_update.html"
    slug_url_kwarg = "column_slug"
    model = models.DataColumn
    fields = ['name']
    success_url = reverse_lazy('setup:local_data_storage:data_domain_overview')


class DeleteDataColumnView(AccessabilityMixin, DataTableMixin, DeleteView):
    model = models.DataColumn
    slug_url_kwarg = "column_slug"
    template_name = "local_data_storage/data_column_delete.html"


##########################


class MigrateView(DataTableMixin, TemplateView):
    template_name = ""