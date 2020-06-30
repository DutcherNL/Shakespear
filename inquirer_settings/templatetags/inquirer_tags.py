from django import template

from Questionaire.models import Inquirer
from inquirer_settings.models import PendingMailVerifyer

register = template.Library()


@register.filter
def has_pending_email_address(inquirer):
    """
    Returns the number of inquiries that are are also not matched
    """
    open_verifyers = PendingMailVerifyer.objects.filter(
        inquirer=inquirer,
        processed=False,
        is_verified=False
    )

    return open_verifyers.first()


