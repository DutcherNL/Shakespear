import datetime

from django.forms import forms, ModelForm, fields, ModelChoiceField
from django.forms.widgets import Textarea

from reports.models import *


class AlterLayoutForm(ModelForm):
    contents = fields.CharField(widget=Textarea(attrs={'style': "width: 100%;"}))

    class Meta:
        model = PageLayout
        fields = ['margins', 'contents']

    def __init__(self, *args, **kwargs):
        super(AlterLayoutForm, self).__init__(*args, **kwargs)

        # self.instance = PageLayout.objects.get()
        self.fields['contents'].initial = self.instance.template_content

    def save(self, commit=True):
        super(AlterLayoutForm, self).save()
        if commit:
            file = self.instance.template
            file.open(mode='tw')
            file.write(self.cleaned_data['contents'])
            file.close()


class LayoutSettingsForm(ModelForm):
    class Meta:
        model = PageLayout
        fields = ['name', 'description']


class SelectPageLayoutForm(ModelForm):

    class Meta:
        model = ReportPage
        fields = ['layout']

    def __init__(self, *args, page=None, **kwargs):
        super(SelectPageLayoutForm, self).__init__(*args, instance=page, **kwargs)


class MovePageForm(forms.Form):
    report_page = ModelChoiceField(queryset=ReportPage.objects.all(), required=True)
    move_up = fields.BooleanField(required=False)

    def __init__(self, *args, report=None, **kwargs):
        self.report = report
        super(MovePageForm, self).__init__(*args, **kwargs)

    def clean_report_page(self):
        report_page = self.cleaned_data['report_page']
        if report_page not in self.report.get_pages():
            raise ValidationError("Page is not part of this report")
        return report_page

    def save(self):
        current_page_number = self.cleaned_data['report_page'].reportpagelink.page_number
        switch_with_link = ReportPageLink.objects. \
            filter(report=self.report). \
            order_by('page_number')

        if self.cleaned_data['move_up']:
            switch_with_link = switch_with_link.\
                filter(page_number__lt=current_page_number).\
                last()
        else:
            switch_with_link = switch_with_link. \
                filter(page_number__gt=current_page_number). \
                first()
        this_page_link = self.cleaned_data['report_page'].reportpagelink
        this_page_link.page_number = switch_with_link.page_number
        this_page_link.save()
        switch_with_link.page_number = current_page_number
        switch_with_link.save()
