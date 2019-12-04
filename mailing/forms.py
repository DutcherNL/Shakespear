from django import forms

from .mails import send_templated_mail



class MailForm(forms.Form):
    to = forms.EmailField()
    subject = forms.CharField(max_length=128)
    text = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        if self.is_valid():
            subject = self.cleaned_data['subject']
            to = {'email': self.cleaned_data['to']}
            context = {'content': self.cleaned_data['text']}
            template_name = "general/basic_mail"

            send_templated_mail(subject,
                                template_name=template_name,
                                context_data=context,
                                recipient=to)
        else:
            raise forms.ValidationError("Form not valid yet")