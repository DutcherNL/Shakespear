from django import forms

from .mails import send_templated_mail


class MailForm(forms.Form):
    """ A simple form to construct and send e-mails """
    to = forms.EmailField()
    subject = forms.CharField(max_length=128)
    text = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        """ Sends the constructed e-mail """
        if self.is_valid():
            subject = self.cleaned_data['subject']
            to = {'email': self.cleaned_data['to']}
            context = {'content': self.cleaned_data['text']}
            template_name = "general/basic_mail"

            # Send the e-mail
            send_templated_mail(subject,
                                template_name=template_name,
                                context_data=context,
                                recipient=to)
        else:
            raise forms.ValidationError("Form not valid yet")