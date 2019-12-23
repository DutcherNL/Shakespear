from django import forms

from .models import BaseModule, TitleModule, TextModule, ImageModule
from .module_registry import registry


def build_moduleform(instance, get_as_class=False, **kwargs):
    """
    Constructs the form for the given module instance
    :param instance: The module instance on which the form should be based
    :param get_as_class: Returns the uninitiated Form class
    :param kwargs: Other Form arguments
    :return: A ModuleForm instance (or class) for the given Module instance
    """
    class_type = type(instance)

    # Create the Form class
    class ModuleForm(forms.ModelForm):
        class Meta:
            model = class_type
            exclude = ['_type', 'information']

    # If uninitiated form is desired
    if get_as_class:
        return ModuleForm

    # Initiate the form
    return ModuleForm(instance=instance, **kwargs)


def get_module_choices(site):
    """ Returns a list of all availlable modules that can be selected """
    module_list = []
    if site is None:
        module_classes = registry.get_all_modules()
    else:
        module_classes = site.get_availlable_modules()

    for module in module_classes:
        module_list.append((module._type_id, module.verbose))
    return module_list


class AddModuleForm(forms.Form):
    """ A form that selects a specific module in a specific location """
    module = forms.ChoiceField(required=True) #choices are defined in __init__
    position = forms.IntegerField(required=True, min_value=1)

    def __init__(self, container=None, site=None, *args, **kwargs):
        """
        Form that opts uses for basic shared module information
        :param container: The container the module is to be placed in
        :param args: Form arguments
        :param kwargs: Form dict arguments
        """
        self.container = container
        super(AddModuleForm, self).__init__(*args, **kwargs)
        self.fields['module'].choices = get_module_choices(site)

    def make_hidden(self):
        """ Sets the form as hidden.

        Contents are still communicated in the background. Unnoticeable for the front-end user
        """
        # Form should be hidden
        for key, field in self.fields.items():
            field.widget = forms.HiddenInput()

    def get_obj_class(self):
        """ Returns the module class of the selected module """
        return registry.get_module(int(self.cleaned_data['module']))

    def get_instance(self):
        if self.is_valid():
            class_type = self.get_obj_class()
            instance = class_type(position=self.cleaned_data['position'],
                                  information=self.container)
            return instance
        return None
