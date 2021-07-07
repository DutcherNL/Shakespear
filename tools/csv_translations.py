import csv
from functools import update_wrapper

from django.http import HttpResponse
from django.db.models import ForeignKey
from django.forms import forms
from django.urls import path
from django.shortcuts import render
from django.views import View
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.auth import get_permission_codename
from django.contrib.contenttypes.models import ContentType


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class ExportCsvInAdminMixin:
    """ A mixin on a model admin that allows for exporting and importing CSV files """

    change_list_template = "admin/change_list_with_csv_options.html"
    actions = ["export_as_csv"]
    replace_csv_fields = []
    exclude_csv_fields = []
    add_csv_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_model_csv_permissions(self.model)

    @staticmethod
    def create_model_csv_permissions(model):
        try:
            # This method can be called prior to the database being set-up, thus the content-type does not exist yet.
            # So catch that error
            content_type = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(
                codename='can_import_csv',
                name='Can import csv files',
                content_type=content_type,
            )
            Permission.objects.get_or_create(
                codename='can_export_csv',
                name='Can export csv files',
                content_type=content_type,
            )
        except Exception:
            pass

    @staticmethod
    def delete_model_csv_permissions(model):
        """ This method can be called from the shell to clean or in code to clean up removed csv mixins """
        content_type = ContentType.objects.get_for_model(model)
        Permission.objects.filter(codename='can_import_csv', content_type=content_type).delete()
        Permission.objects.filter(codename='can_export_csv', content_type=content_type).delete()

    def get_urls(self):
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        my_urls = [
            path('import-csv/', wrap(self.import_csv_view), name='%s_%s_import_csv' % info),
            path('export-csv/', wrap(self.export_all_as_csv), name='%s_%s_export_csv' % info),
        ]
        return my_urls + urls

    def has_csv_permission(self, request, perm_name):
        """
        Return True if the given request has permission to add an object.
        Can be overridden by the user in subclasses.
        """
        opts = self.opts
        codename = get_permission_codename(perm_name, opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def import_csv_view(self, request):
        """ Present a view for importing CSV objects """
        if not self.has_csv_permission(request, 'can_import_csv'):
            raise PermissionDenied

        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                incorrect_lines = self.process_csv_import(request)

                if len(incorrect_lines) == 0:
                    self.message_user(request, "Your csv file has been imported")
                else:
                    self.message_user(request, f"CSV file has been processed,"
                                               f"but produced errors on the following lines: {incorrect_lines}")
                return self._response_post_save(request, None)
        else:
            form = CsvImportForm()

        opts = self.model._meta
        app_label = opts.app_label

        cl = self.get_changelist_instance(request)

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            'module_name': str(opts.verbose_name_plural),
            'opts': opts,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': self.actions_selection_counter,
            'preserved_filters': self.get_preserved_filters(request),
            'title': 'Import csv file',
            'has_add_permission': self.has_add_permission(request),
        }

        return render(
            request, "admin/csv_form.html", context
        )

    def process_csv_import(self, request):
        # POST method is used. So process the CSV file
        # Get the CSV file, fix the encoding and place it in a dictreader object
        csv_file = request.FILES["csv_file"]
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)

        # Get the foreign key relations
        # Searches any object with a double underscore as that indicates a link.
        f_keys = {}
        for field in reader.fieldnames:
            f = field.split('__', 1)
            if len(f) == 2:
                # If a foreign key is found, set the related argument name.
                # As there could be multiple arguments, it is placed in a list.
                f_keys[f[0]] = f_keys.get(f[0], [])
                f_keys[f[0]].append(f[1])

        # Track the index and report any errors
        line_number = 1
        incorrect_lines = []
        # Process all lines in the file
        for row in reader:
            init_kwargs = row

            line_error = None

            # Get the foreign related objects
            for f_key, f_link in f_keys.items():
                # Set the keywords for the search query
                # This is anything that followed the first __ as that indicates the initial link
                f_search_kwargs = {}
                for param in f_link:
                    f_search_kwargs[param] = init_kwargs.pop(f'{f_key}__{param}')

                # Get the foreign model
                foreign_model = getattr(self.model, f_key).field.remote_field.model
                # Filter the foreign model
                f_model = foreign_model.objects.filter(**f_search_kwargs)
                if f_model.count() == 1:
                    init_kwargs[f_key] = f_model.first()
                elif f_model.count() == 0:
                    line_error = f"Related object {f_key} was not found"
                else:
                    line_error = f"Related object {f_key} returned multiple answers"

            if line_error is None:
                obj = self.model(**init_kwargs)
                try:
                    obj.full_clean()
                except ValidationError as e:
                    line_error = e
                else:
                    obj.save()

            if line_error:
                incorrect_lines.append((line_number, line_error))

            line_number += 1

        return incorrect_lines

    def export_all_as_csv(self, request):
        return self.export_as_csv(request, self.model.objects.all())

    def export_as_csv(self, request, queryset):
        """ Exports a queryset of objects to a csv file """

        if not self.has_csv_permission(request, 'can_export_csv'):
            raise PermissionDenied

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        # Remove id parameter (not needed outside of db)
        field_names.remove('id')
        # Remove other fields
        for exclude_field in self.exclude_csv_fields:
            field_names.remove(exclude_field)

        # Search any foreign keys and try to get a proper foreign key link for it.
        # This can not be the normal id as this can not be quarenteed when inserting it on a new model.
        for field in meta.fields:
            if field.name in field_names and isinstance(field, ForeignKey):
                foreign_model = field.remote_field.model
                field_names.remove(field.name)
                if hasattr(foreign_model, "name"):
                    field_names.append(f'{field.name}__name')
                elif hasattr(foreign_model, "slug"):
                    field_names.append(f'{field.name}__slug')
                else:
                    raise KeyError(f"foreign key {0} can not be linked. It does not have either a name or a slug. "
                                   f"Remove the field from the export with the exclude_field property "
                                   f"or have a name or slug property on the {foreign_model} model")
        # Add fields
        for add_field in self.add_csv_fields:
            field_names.append(add_field)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            data = []
            for field in field_names:
                field = field.split('__')
                entry = obj
                for attribute in field:
                    entry = getattr(entry, attribute)

                data.append(entry)

            row = writer.writerow(data)

        return response

    export_as_csv.short_description = "Export Selected in csv file"


class CSVView(View):
    http_method_names = ['get']
    filename = None
    header_fields = None

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={self.get_filename()}'
        writer = csv.writer(response)

        # Define the header
        writer.writerow(self.get_header())

        # Write the data
        for data in self.get_csv_data():
            writer.writerow(data)

        return response

    def get_filename(self):
        """ Returns the filename of the file as defined in 'self.filename' """
        if self.filename is None:
            raise KeyError("Filename for csv is not defined")
        filename = self.filename
        if not self.filename.endswith('.csv'):
            filename += '.csv'

    def get_header(self):
        """ Returns the header as defined in 'header_fields' or a custom design if method is overwritten"""
        if self.header_fields is None:
            raise KeyError(f"{self.__class__.__name__} has no attribute for 'header_fields' defined. "
                           f"Define this attribute or overwrite the get_header method.")
        if not hasattr(self.header_fields, '__iter__'):
            raise KeyError(f"{self.__class__.__name__} returns a non-iterable instance for 'header_fields'. Ensure it "
                           f"is iterable by having it as a list or tuple.")
        return self.header_fields

    def get_csv_data(self):
        """ Returns an iterable of iterables with all the values of the fields supposed to go in the CSV file"""
        raise NotImplementedError(f"{self.__class__.__name__} has 'get_csv_data' not yet defined")
