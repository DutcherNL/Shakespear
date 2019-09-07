from django.contrib import admin

from .models import Information, BaseModule, TitleModule, TextModule, ImageModule

# Register your models here.


class InformationAdmin(admin.ModelAdmin):
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


admin.site.register(Information, InformationAdmin)
admin.site.register(BaseModule)
admin.site.register(TitleModule)
admin.site.register(TextModule)
admin.site.register(ImageModule)
