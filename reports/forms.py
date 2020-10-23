from django.forms import forms, ModelForm, fields
from django.forms.widgets import Textarea

from reports.models import PageLayout


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


