from django.views.generic import View, TemplateView, ListView, FormView, DetailView
from django.views.generic.edit import UpdateView, DeleteView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden

from local_data_storage import models
from local_data_storage.forms import DataUploadForm, FilterDataForm
from queued_tasks.models import QueuedCSVDataProcessingTask

from tools import pagination


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
    fields = ['name', 'description', 'key_column_name', 'key_regex']


class DataTableDetailRedirectView:
    """ A view that acts as a shell for internal view redirection"""
    @classmethod
    def as_view(cls, **initkwargs):
        def view(request, *args, **kwargs):
            data_table = get_object_or_404(models.DataTable, slug=kwargs['table_slug'])
            if data_table.is_active:
                return DataTableActiveView.as_view(**initkwargs)(request, *args, **kwargs)
            else:
                return DataTableInactiveView.as_view(**initkwargs)(request, *args, **kwargs)
        return view


class DataTableInactiveView(AccessabilityMixin, DetailView):
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
    fields = ['name', 'description', 'key_column_name', 'key_regex']


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
        else:
            return super(DataTableDeclarationEditMixin, self).dispatch(request, *args, **kwargs)


class AddDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, CreateView):
    model = models.DataColumn
    template_name = "local_data_storage/data_column_add.html"
    fields = ['name', 'column_type']

    def form_valid(self, form):
        form.instance.table = self.data_table
        return super(AddDataColumnView, self).form_valid(form)


class UpdateDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, UpdateView):
    template_name = "local_data_storage/data_column_update.html"
    slug_url_kwarg = "column_slug"
    model = models.DataColumn
    fields = ['name', 'column_type']
    success_url = reverse_lazy('setup:local_data_storage:data_domain_overview')


class DeleteDataColumnView(AccessabilityMixin, DataTableMixin, DataTableDeclarationEditMixin, DeleteView):
    model = models.DataColumn
    slug_url_kwarg = "column_slug"
    template_name = "local_data_storage/data_column_delete.html"


##########################


class FilterDataMixin:
    paginator_class = pagination.FlexPaginator

    def dispatch(self, request, *args, **kwargs):
        self.filter_form = FilterDataForm(data_table=self.data_table, data=self.request.GET)
        return super(FilterDataMixin, self).dispatch(request, *args, **kwargs)

    def get_page_list(self):
        return range()

    def get_context_data(self, **kwargs):
        context = super(FilterDataMixin, self).get_context_data(**kwargs)

        context.update({
            'filter_form': self.filter_form,
            'search_q': self.filter_form.filter_url_kwargs,
        })
        return context


class DataTableActiveView(AccessabilityMixin, DataTableMixin, FilterDataMixin, ListView):
    template_name = "local_data_storage/data_table_info_post_migrate.html"
    context_object_name = "data_objects"
    paginate_by = 25

    def get_queryset(self):
        queryset = self.data_table.get_data_table_entries()
        return self.filter_form.filter(queryset)


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
        self.fields.append(self.data_table.db_key_column_name)
        for column in self.data_table.datacolumn_set.all():
            self.fields.append(column.db_column_name)
        return super(AddDataView, self).get_form_class()


# class AddCSVDataView(DataTableMixin, DataEditMixin, FormView):
#     template_name = 'local_data_storage/data_entry_csv_add.html'
#     form_class = DataUploadForm
#
#     def get_form_kwargs(self):
#         kwargs = super(AddCSVDataView, self).get_form_kwargs()
#         kwargs['data_table'] = self.data_table
#         return kwargs
#
#     def form_valid(self, form):
#         # This method is called when valid form data has been POSTed.
#         # It should return an HttpResponse.
#         form.process_csv_file()
#         return super().form_valid(form)


class AddCSVDataView(AccessabilityMixin, DataTableMixin, CreateView):
    model = QueuedCSVDataProcessingTask
    template_name = 'local_data_storage/data_entry_csv_add.html'
    fields = ['csv_file', 'data_table', 'overwrite_with_empty', 'deliminator']

    def form_valid(self, form):
        form.instance.data_table = self.data_table
        return super(AddCSVDataView, self).form_valid(form)



class UpdateDataView(DataTableMixin, DataEditMixin, UpdateView):
    template_name = "local_data_storage/data_entry_update.html"
    pk_url_kwarg = 'data_id'

    def get_form_class(self):
        self.fields = []
        for column in self.data_table.datacolumn_set.all():
            self.fields.append(column.db_column_name)
        return super(UpdateDataView, self).get_form_class()


class DeleteDataView(DataTableMixin, DataEditMixin, DeleteView):
    template_name = "local_data_storage/data_entry_delete.html"
    pk_url_kwarg = 'data_id'
