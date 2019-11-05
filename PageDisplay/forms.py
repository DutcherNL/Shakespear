from django import forms

from .models import BaseModule, TitleModule, TextModule, ImageModule
from .module_registry import registry


def build_moduleform(instance, **kwargs):
    class_type = type(instance)

    class ModuleForm(forms.ModelForm):
        class Meta:
            model = class_type
            exclude = ['_type', 'information']

    return ModuleForm(instance=instance, **kwargs)


def get_module_choices():
    module_list = []
    module_classes = registry.get_all_modules()

    for module in module_classes:
        module_list.append((module._type_id, module.verbose))
    return module_list


class AddModuleForm(forms.Form):
    module = forms.ChoiceField(choices=get_module_choices())
    position = forms.IntegerField(initial=1)

    def __init__(self, page=None, *args, **kwargs):
        if page:
            self.page = page
        super(AddModuleForm, self).__init__(*args, **kwargs)

    def save(self):
        class_name = registry.get_module(int(self.cleaned_data['module']))
        self.instance = class_name(position=self.cleaned_data['position'], information=self.page)
        self.instance.save()
        return self.instance


class DelModuleForm(forms.Form):

    def __init__(self, module_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = BaseModule.objects.get(id=module_id)

    def clean(self):
        # Ready for more advanced logic
        a = super().clean()
        print("Clean {0}".format(a))
        return a

    def execute(self):
        print("Delete module")

        self.module.delete()
