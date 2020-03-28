from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template, TemplateDoesNotExist


def construct_and_send_mail(mail_page, context, to, **kwargs):
    rendered_page = mail_page.render(**context)

    send_mail(subject=mail_page.title,
              txt_template="Temporary placeholder",
              html_template=rendered_page,
              to=[to], **kwargs)
    pass


def send_mail(*args, txt_template=None, html_template=None, fail_silently=False, **kwargs):
    # Set up the Email template with the txt_template
    mail_obj = EmailMultiAlternatives(*args, **kwargs, body=txt_template)

    # Set up the html content in the mail
    mail_obj.attach_alternative(html_template, "text/html")

    # Send the mail
    mail_obj.send(fail_silently=fail_silently)