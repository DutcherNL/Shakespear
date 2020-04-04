from django.views.generic import TemplateView, ListView, FormView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden

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
    slug_url_kwarg = "table_slug"
    model = models.DataTable
    context_object_name = "data_table"

    def get_template_names(self):
        if not self.object.is_active:
            return "local_data_storage/data_table_info_pre_migrate.html"
        else:
            return "local_data_storage/data_table_info_post_migrate.html"


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


class DataTableDeclarationEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.data_table.is_active:
            return HttpResponseForbidden("Datatable is active and can not be edited")


class AddDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, CreateView):
    model = models.DataColumn
    template_name = "local_data_storage/data_column_add.html"
    fields = ['name']

    def form_valid(self, form):
        form.instance.table = self.data_table
        return super(AddDataColumnView, self).form_valid(form)


class UpdateDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, UpdateView):
    template_name = "local_data_storage/data_column_update.html"
    slug_url_kwarg = "column_slug"
    model = models.DataColumn
    fields = ['name']
    success_url = reverse_lazy('setup:local_data_storage:data_domain_overview')


class DeleteDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, DeleteView):
    model = models.DataColumn
    slug_url_kwarg = "column_slug"
    template_name = "local_data_storage/data_column_delete.html"


##########################


class MigrateView(DataTableMixin, TemplateView):
    template_name = "local_data_storage/data_table_migrate.html"

    def post(self, request, *args, **kwargs):
        if not self.data_table.is_active:
            self.data_table.create_table_on_db()
        else:
            self.data_table.destroy_table_on_db()

        return HttpResponseRedirect(self.data_table.get_absolute_url())


##########################

class DataEditMixin:
    def dispatch(self, *args, **kwargs):
        self.model = self.data_table.get_data_class()

        if not self.data_table.is_active:
            return HttpResponseForbidden("Datatable is not active and thus data can not be altered")
        return super(DataEditMixin, self).dispatch(*args, **kwargs)


class AddDataView(DataTableMixin, DataEditMixin, CreateView):
    template_name = "local_data_storage/data_entry_add.html"

    def get_form_class(self):
        self.fields = []
        for column in self.data_table.datacolumn_set.all():
            self.fields.append(column.slug)
        return super(AddDataView, self).get_form_class()


class UpdateDataView(DataTableMixin, DataEditMixin, UpdateView):
    template_name = "local_data_storage/data_entry_update.html"
    pk_url_kwarg = 'data_id'

    def get_form_class(self):
        self.fields = []
        for column in self.data_table.datacolumn_set.all():
            self.fields.append(column.slug)
        return super(UpdateDataView, self).get_form_class()


class DeleteDataView(DataTableMixin, DataEditMixin, DeleteView):
    pk_url_kwarg = 'data_id'
