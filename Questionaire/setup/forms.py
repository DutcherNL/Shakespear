from django import forms
from django.forms import ValidationError

from Questionaire.models import Technology
from PageDisplay.models import Page, VerticalModuleContainer, TitleModule, TextModule


class CreatePageForTechForm(forms.Form):
    technology = forms.ModelChoiceField(queryset=Technology.objects.all(), required=True)

    def clean(self):
        if self.cleaned_data['technology'].information_page is not None:
            raise ValidationError("Technology already has a page associated with it")

    def save(self):
        if self.is_valid():
            tech = self.cleaned_data['technology']

            # Create the page content
            container = VerticalModuleContainer.objects.create()
            TitleModule.objects.create(position=1, information=container, size=1, title=tech.name)
            TextModule.objects.create(position=2, information=container, text=tech.short_text)
            page = Page.objects.create(name=tech.name, layout=container)
            tech.information_page = page
            tech.save()
