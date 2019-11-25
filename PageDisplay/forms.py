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
    module = forms.ChoiceField(choices=get_module_choices(), required=True)
    position = forms.IntegerField(required=True)

    def __init__(self, container=None, *args, **kwargs):
        self.container = container
        super(AddModuleForm, self).__init__(*args, **kwargs)

    def make_hidden(self):
        # Form should be hidden
        for key, field in self.fields.items():
            field.widget = forms.HiddenInput()

    def clean_position(self):
        position = self.cleaned_data['position']
        if position <= 0:
            raise forms.ValidationError("Position must be larger than 0")
        return position

    def get_obj_class(self):
        return registry.get_module(int(self.cleaned_data['module']))

    def get_instance(self):
        if self.is_valid():
            class_type = self.get_obj_class()
            instance = class_type(position=self.cleaned_data['position'],
                                  information=self.container)
            return instance
        return None

    def save(self):
        class_name = registry.get_module(int(self.cleaned_data['module']))
        # self.instance = class_name(position=self.cleaned_data['position'], information=self.page)
        # self.instance.save()
        return self.instance


class DelModuleForm(forms.Form):

    def __init__(self, module_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = BaseModule.objects.get(id=module_id)

    def execute(self):
        self.module.delete()
