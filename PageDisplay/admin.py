from django.contrib import admin

from .models import *

# Register your models here.


@admin.register(BaseModule)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_type_name', 'get_type_str')

    def get_type_name(self, obj):
        return obj.get_child().type

    def get_type_str(self, obj):
        return obj.get_child().__str__()


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'root_module', 'last_edited')


@admin.register(ContainerModulePositionalLink)
class ContainerLinkAdmin(admin.ModelAdmin):
    list_display = ('id', 'container', 'module')


admin.site.register(VerticalContainerModule)
admin.site.register(TitleModule)
admin.site.register(TextModule)
admin.site.register(ImageModule)
