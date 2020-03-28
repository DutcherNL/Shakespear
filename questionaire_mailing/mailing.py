from django.core.mail import EmailMultiAlternatives, get_connection

from questionaire_mailing.renderers import MailPlainRenderer


def construct_and_send_mail(mail_page, context, to, **kwargs):
    rendered_html_page = mail_page.render(**context)
    rendered_plain_page = mail_page.render(renderer=MailPlainRenderer, **context)

    send_mail(subject=mail_page.title,
              txt_template=rendered_plain_page,
              html_template=rendered_html_page,
              to=[to], **kwargs)
    pass


def send_mail(*args, txt_template=None, html_template=None, fail_silently=False, **kwargs):
    # Set up the Email template with the txt_template
    mail_obj = EmailMultiAlternatives(*args, **kwargs, body=txt_template)

    # Set up the html content in the mail
    mail_obj.attach_alternative(html_template, "text/html")

    # Send the mail
    mail_obj.send(fail_silently=fail_silently)