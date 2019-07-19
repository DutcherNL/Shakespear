from django.contrib import admin
from .models import StoredDataContent, StoredDataCodeDeclaration, StoredDataDeclaration, StoredDataCode

# Register your models here.


class StoredDataAdmin(admin.ModelAdmin):
    class ContentInline(admin.TabularInline):
        model = StoredDataContent
        extra = 0

    inlines = [ContentInline]


admin.site.register(StoredDataCodeDeclaration)
admin.site.register(StoredDataCode, StoredDataAdmin)
admin.site.register(StoredDataDeclaration)
