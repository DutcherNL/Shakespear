from django.conf import settings

from Questionaire.models import Inquirer


def questionaire_context(request):
    """Adds some variables to every template context."""
    context = {
        # Get the current inquirer session
        'inquirer': Inquirer.objects.filter(id=request.session.get('inquirer_id', None)).first(),
    }
    # Set some attributes from the settings in the glocal context
    context.update({
        'DISPLAY_TECH_SCORES': settings.DISPLAY_TECH_SCORES_IN_VIEW,
        'SITE_DISPLAY_NAME': settings.SITE_DISPLAY_NAME,
        'MAIN_CONTACT_EMAIL': settings.MAIN_CONTACT_EMAIL,
        'PRIVACY_DOCUMENT_URL': settings.PRIVACY_DOCUMENT_URL
    })



    return context


def pdf_context(request):
    return {
        # A correction for the font size in PDF templates
        'PDF_BASE_FONT_SIZE': settings.PDF_BASE_FONT_SIZE
    }

