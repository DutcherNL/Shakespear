from django.forms import forms, ModelForm

from .models import TitleModule


def build_moduleform(instance, **kwargs):
    class_type = type(instance)

    class ModuleForm(ModelForm):
        class Meta:
            model = class_type
            exclude = ['_type', 'information']

    return ModuleForm(instance=instance, **kwargs)
