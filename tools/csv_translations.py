import csv

from django.http import HttpResponse
from django.forms import forms
from django.urls import path
from django.shortcuts import render
from django.core.exceptions import ValidationError


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


class ExportCsvMixin:
    """ A mixin on a model admin that allows for exporting and importing CSV files """

    change_list_template = "admin/change_list_with_csv_options.html"
    actions = ["export_as_csv"]
    replace_csv_fields = []
    exclude_csv_fields = []
    add_csv_fields = []

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
            path('export-csv/', self.export_all_as_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        """ Present a view for importing CSV objects """
        if request.method == "POST":
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
                        pass
                        obj.save()

                if line_error:
                    incorrect_lines.append((line_number, line_error))

                line_number += 1

            if len(incorrect_lines) == 0:
                self.message_user(request, "Your csv file has been imported")
            else:
                self.message_user(request, f"CSV file has been processed,"
                                           f"but produced errors on the following lines: {incorrect_lines}")
            #return self._response_post_save(request, None)

        opts = self.model._meta
        app_label = opts.app_label

        cl = self.get_changelist_instance(request)

        context = {
            **self.admin_site.each_context(request),
            "form": CsvImportForm(),
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

    def export_all_as_csv(self, request):
        return self.export_as_csv(request, self.model.objects.all())

    def export_as_csv(self, request, queryset):
        """ Exports a queryset of objects to a csv file """

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        # Remove id parameter (not needed outside of db)
        field_names.remove('id')
        # Remove other fields
        for exclude_field in self.exclude_csv_fields:
            field_names.remove(exclude_field)
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