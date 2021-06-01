from django import forms

from .mails import send_templated_mail


class MailForm(forms.Form):
    """ A simple form to construct and send e-mails """
    to = forms.EmailField()
    subject = forms.CharField(max_length=128)
    text = forms.CharField(widget=forms.Textarea)

    # Ingore the to-field in cleaning. This way the field can be used for symbolised targets
    ignore_to_field = False

    def _clean_fields(self):
        super(MailForm, self)._clean_fields()
        if self.ignore_to_field:
            if 'to' in self.errors.keys():
                del self.errors['to']

    def send_email(self):
        """ Sends the constructed e-mail """
        if self.is_valid():
            subject = self.cleaned_data['subject']
            to = {'email': self.get_to_adresses()}
            context = {'content': self.cleaned_data['text']}
            template_name = "general/basic_mail"

            # Send the e-mail
            send_templated_mail(subject,
                                template_name=template_name,
                                context_data=context,
                                recipient=to)
        else:
            raise forms.ValidationError("Form not valid yet")

    def get_to_adresses(self):
        return self.cleaned_data['to']
