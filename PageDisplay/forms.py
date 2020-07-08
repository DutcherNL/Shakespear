from django import forms
from django.db.models import F

from .models import BaseModule, ContainerModulePositionalLink
from .module_registry import registry
from .widgets import ModulePositionInput


def scootch_module_at(container_id, position):
    if ContainerModulePositionalLink.objects.filter(position=position+1, container_id=container_id).count() > 0:
        scootch_module_at(container_id, position+1)
    ContainerModulePositionalLink.objects.filter(position=position, container_id=container_id).update(position=F('position')+1)


def resolve_module_conflicts(module, container_id):
    """ Resolves conflicts in positions between modules. Making sure that no module will be in the same position """
    conflicted_modules = ContainerModulePositionalLink.objects.filter(container_id=module.information_id,
                                                   position=module.position).exclude(id=module.id)
    for conflict in conflicted_modules:
        scootch_module_at(module.information_id, module.position+1)
        conflict.position = F('position')+1
        conflict.save(update_fields=['position'])


def build_moduleform(instance, get_as_class=False, exclude_fields=[], **kwargs):
    """
    Constructs the form for the given module instance
    :param exclude_fields: A list of fields that should be excluded from the form
    :param instance: The module instance on which the form should be based
    :param get_as_class: Returns the uninitiated Form class
    :param kwargs: Other Form arguments
    :return: A ModuleForm instance (or class) for the given Module instance
    """
    class_type = type(instance)
    exclude_fields = ['_type', *exclude_fields]

    # Create the Form class
    class ModuleForm(forms.ModelForm):
        class Meta:
            model = class_type
            exclude = exclude_fields

    # If uninitiated form is desired
    if get_as_class:
        return ModuleForm

    # Initiate the form
    return ModuleForm(instance=instance, **kwargs)


def get_module_choices(site):
    """ Returns a list of all availlable modules that can be selected """
    module_list = []
    if site is None:
        module_classes = registry.get_module_list()
    else:
        module_classes = site.get_availlable_modules()

    for module in module_classes:
        module_list.append((module._type_id, module.verbose))
    return module_list


class AddModuleForm(forms.Form):
    """ A form that selects a specific module in a specific location """
    module = forms.ChoiceField(required=True)  # choices are defined in __init__
    field_name = forms.CharField(max_length=64, widget=forms.HiddenInput)

    def __init__(self, site=None, *args, **kwargs):
        """
        Form that opts uses for basic shared module information
        :param container: The container the module is to be placed in
        :param args: Form arguments
        :param kwargs: Form dict arguments
        """
        super(AddModuleForm, self).__init__(*args, **kwargs)
        self.fields['module'].choices = get_module_choices(site)

    def make_hidden(self):
        """ Sets the form as hidden.

        Contents are still communicated in the background. Unnoticeable for the front-end user
        """
        # Form should be hidden
        for key, field in self.fields.items():
            field.widget = forms.HiddenInput()

    def get_instance(self):
        if self.is_valid():
            class_type = registry.get_module(int(self.cleaned_data['module']))
            instance = class_type()
            return instance
        return None


class ModuleLinkForm(forms.ModelForm):
    class Meta:
        model = ContainerModulePositionalLink
        fields = ('container', 'position')
        widgets = {
            'position': ModulePositionInput,
            'container': forms.HiddenInput,
        }

    def save(self, module):
        try:
            link = ContainerModulePositionalLink.objects.get(module=module, container=self.cleaned_data['container'])
        except ContainerModulePositionalLink.DoesNotExist:
            link = ContainerModulePositionalLink(module=module, container=self.cleaned_data['container'])
        link.position = self.cleaned_data['position']
        link.save()
        return link
