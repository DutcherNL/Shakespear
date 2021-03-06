from django import forms
from django.forms import ValidationError

from Questionaire.models import Technology, PageEntry
from Questionaire.models import Page as InquiryPage
from Questionaire.modules.modules import QuestionModule
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


class CreateInquiryDisplayPageForm(forms.Form):
    inquiry_page = forms.ModelChoiceField(queryset=InquiryPage.objects.all(), required=True)

    def clean(self):
        if self.cleaned_data['inquiry_page'].display_page is not None:
            raise ValidationError("Inquiry Page already has a display page")

    def save(self):
        if self.is_valid():
            inquiry_page = self.cleaned_data['inquiry_page']

            # Create the page content
            container = VerticalContainerModule.objects.create()
            page = Page.objects.create(name=inquiry_page.name, root_module=container)

            page_entries = PageEntry.objects.filter(page=inquiry_page).order_by('position')

            for i, page_element in enumerate(page_entries, start=1):
                if page_element.entry_type == 1:
                    text_element = page_element.pageentrytext
                    module = TextModule.objects.create(text=text_element.text)
                elif page_element.entry_type == 2:
                    question_element = page_element.pageentryquestion
                    module = QuestionModule.objects.create(
                        question=question_element.question,
                        required=question_element.required,
                    )

                ContainerModulePositionalLink.objects.create(
                    container=container,
                    position=i*10,
                    module=module,
                )

            inquiry_page.display_page = page
            inquiry_page.save()