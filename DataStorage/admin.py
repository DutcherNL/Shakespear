from django.contrib import admin
from .models import StoredDataContent, StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataCode, DataBatch
from .forms import DataUploadForm
from django.shortcuts import render

# Register your models here.


class DataBatchAdmin(admin.ModelAdmin):
    """ The Admin control for the DataBatch model """
    # Use the DataUpload Form to allow bulk uploading through csv files
    form = DataUploadForm
    csv_errors = False
    csv_error_template = "datastorage/admin_show_batch_results.html"

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        instance, self.csv_errors = form.save(commit=False, return_with_errors=True)
        return instance

    def save_related(self, request, form, formsets, change):
        super(DataBatchAdmin, self).save_related(request, form, formsets, change)
        self.csv_errors = form.process_csv_file(commit=True)

    def response_add(self, request, obj, post_url_continue=None):
        if self.csv_errors is None:
            return super(DataBatchAdmin, self).response_add(request, obj, post_url_continue)
        return self.render_batch_errors(request, obj)

    def response_change(self, request, obj):
        if self.csv_errors is None:
            return super(DataBatchAdmin, self).response_change(request, obj)
        return self.render_batch_errors(request, obj)

    def render_batch_errors(self, request, obj):
        opts = self.model._meta

        print(self.media)

        context = {
            **self.admin_site.each_context(request),
            'module_name': str(opts.verbose_name_plural),
            'opts': opts,
            'original': obj,
            'media': self.media,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': self.actions_selection_counter,
            'preserved_filters': self.get_preserved_filters(request),
            'title': 'CSV errors',
            'has_add_permission': self.has_add_permission(request),
            'csv_errors': self.csv_errors
        }

        return render(request, self.csv_error_template, context)


class StoredDataAdmin(admin.ModelAdmin):
    class ContentInline(admin.TabularInline):
        model = StoredDataContent
        extra = 0
    inlines = [ContentInline]


class StoredDataCodeAdmin(admin.ModelAdmin):
    class ContentDeclarationInline(admin.TabularInline):
        model = StoredDataDeclaration
        extra = 0
    inlines = [ContentDeclarationInline]


admin.site.register(StoredDataCodeDeclaration, StoredDataCodeAdmin)
admin.site.register(StoredDataCode, StoredDataAdmin)
admin.site.register(DataBatch, DataBatchAdmin)
