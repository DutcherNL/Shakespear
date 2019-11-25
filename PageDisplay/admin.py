from django.contrib import admin

from .models import VerticalModuleContainer, Page, TitleModule, TextModule, ImageModule, ModuleContainer

# Register your models here.


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


admin.site.register(VerticalModuleContainer, VertContainerAdmin)
admin.site.register(ModuleContainer)
admin.site.register(Page)
admin.site.register(TitleModule)
admin.site.register(TextModule)
admin.site.register(ImageModule)
