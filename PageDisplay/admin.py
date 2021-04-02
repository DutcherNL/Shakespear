from django.contrib import admin

from .models import *

# Register your models here.


@admin.register(VerticalContainerModule)
class VertContainerAdmin(admin.ModelAdmin):
    class TitleInlines(admin.TabularInline):
        model = TitleModule
        extra = 0
        exclude = ('_type',)

    class TextsInlines(admin.TabularInline):
        model = TextModule
        extra = 0
        exclude = ('_type',)

    class ImageInlines(admin.TabularInline):
        model = ImageModule
        extra = 0
        exclude = ('_type',)

    inlines = [TitleInlines, TextsInlines, ImageInlines]


@admin.register(BaseModule)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_type_name', 'get_type_str')

    def get_type_name(self, obj):
        return obj.get_child().type

    def get_type_str(self, obj):
        return obj.get_child().__str__()


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'last_edited')

admin.site.register(TitleModule)
admin.site.register(TextModule)
admin.site.register(ImageModule)

admin.site.register(ContainerModulePositionalLink)
