from django import forms

from .models import BaseModule, TitleModule, TextModule, ImageModule


def build_moduleform(instance, **kwargs):
    class_type = type(instance)

    class ModuleForm(forms.ModelForm):
        class Meta:
            model = class_type
            exclude = ['_type', 'information']

    return ModuleForm(instance=instance, **kwargs)


def get_module_choices(modules):
    module_list = []
    for i in range(len(modules)):
        module_list.append((i, modules[i].verbose))
    return module_list


class AddModuleForm(forms.Form):
    _modules = [TitleModule, TextModule, ImageModule]

    module = forms.ChoiceField(choices=get_module_choices(_modules))
    position = forms.IntegerField(initial=1)

    def __init__(self, page=None, *args, **kwargs):
        if page:
            self.page = page
        super(AddModuleForm, self).__init__(*args, **kwargs)

    def save(self):
        class_name = self._modules[int(self.cleaned_data['module'])]
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
