from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import get_template, TemplateDoesNotExist


def _render_and_send_mail(*args, txt_template=None, html_template=None, context_data={}, fail_silently=False, **kwargs):
    # Set up the Email template with the txt_template
    mail_obj = EmailMultiAlternatives(*args, **kwargs, body=txt_template.render(context_data))

    # Set up the html content in the mail
    if html_template is not None:
        content_html = html_template.render(context_data)
        mail_obj.attach_alternative(content_html, "text/html")

    # Send the mail
    mail_obj.send(fail_silently=fail_silently)


def _get_mail_templates(full_template_name):
    """ Gets the mail template with the given name """
    try:
        return get_template(full_template_name, using='EmailTemplates')
    except TemplateDoesNotExist:
        return None


def send_templated_mail(subject=None, template_name=None, context_data={}, recipient=None, **kwargs):
    """
    Sends a templated e-mail to the recipient
    :param subject: The subject of the mail
    :param template_name: The template name without extension. Assumes a .txt version exists for plain text
     and uses .html file if one is present at the same location
    :param context_data: The context data used in the rendering process.
     User is automatically added as 'user' if it is a Django model instance
    :param recipient: The recipient.
     Can be a string of an email adres or a dict/ Django model object with an email parameter
    :param kwargs: additional EmailTemplateMessage arguments (from django.core.email)
    :return: --
    """
    if recipient is None:
        raise KeyError("No email target given. Please define the recipient")

    # Get the email
    if isinstance(recipient, dict):
        to = recipient.get('email', None)
    elif isinstance(recipient, str):
        to = recipient
    else:
        to = recipient.email
        context_data['user'] = recipient

    # Render and send the e-mail
    _render_and_send_mail(subject=subject,
                          txt_template=_get_mail_templates(template_name+".txt"),
                          html_template=_get_mail_templates(template_name+".html"),
                          context_data=context_data,
                          to=[to], **kwargs)


def send_templated_mass_mail(subject=None, template_name=None, context_data={}, recipients=None, **kwargs):
    """
    Send a mass mail to all recipients with an EmailTemplateMessage as the message created
    :param subject: The email subject or header
    :param template_name: The name of the template
    :param context_data: the context data for the mail
    :param recipients: The queryset of users
    :param kwargs: additional EmailTemplateMessage arguments
    """

    # Get the templates
    txt_template = _get_mail_templates(template_name+".txt")
    html_template = _get_mail_templates(template_name+".html")

    # Open the connection
    connection = get_connection()
    connection.open()

    for recipient in recipients:
        # Set the user in the context data
        context_data['user'] = recipient
        to = [recipient.email]

        _render_and_send_mail(subject=subject,
                              txt_template=txt_template,
                              html_template=html_template,
                              context_data=context_data,
                              to=to, **kwargs)
    connection.close()




