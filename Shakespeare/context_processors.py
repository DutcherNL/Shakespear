from django.conf import settings


def questionaire_context(request):
    """Adds some variables to every template context."""
    context = {}
    context['DISPLAY_TECH_SCORES'] = settings.DISPLAY_TECH_SCORES_IN_VIEW

    context['SITE_DISPLAY_NAME'] = settings.SITE_DISPLAY_NAME
    context['MAIN_CONTACT_EMAIL'] = settings.MAIN_CONTACT_EMAIL

    context['PRIVACY_DOCUMENT_URL'] = settings.PRIVACY_DOCUMENT_URL
    return context


def pdf_context(request):
    return {
        # A correction for the font size in PDF templates
        'PDF_BASE_FONT_SIZE': settings.PDF_BASE_FONT_SIZE
    }

