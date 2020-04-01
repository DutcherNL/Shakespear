from django import forms
from django.forms import ValidationError

from Questionaire.models import Technology
from PageDisplay.models import Page, VerticalContainerModule, TitleModule, TextModule, ContainerModulePositionalLink


class CreatePageForTechForm(forms.Form):
    technology = forms.ModelChoiceField(queryset=Technology.objects.all(), required=True)

    def clean(self):
        if self.cleaned_data['technology'].information_page is not None:
            raise ValidationError("Technology already has a page associated with it")

    def save(self):
        if self.is_valid():
            tech = self.cleaned_data['technology']

            # Create the page content
            container = VerticalContainerModule.objects.create()
            ContainerModulePositionalLink(container=container,
                                          position=50,
                                          module=TitleModule.objects.create(size=1, title=tech.name)).save()
            ContainerModulePositionalLink(container=container,
                                          position=100,
                                          module=TextModule.objects.create(text=tech.short_text)).save()
            page = Page.objects.create(name=tech.name, root_module=container)
            tech.information_page = page
            tech.save()
