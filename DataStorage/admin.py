from django.contrib import admin
from .models import StoredDataContent, StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataCode

# Register your models here.


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
