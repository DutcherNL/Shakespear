from django.conf import settings


def questionaire_context(request):
    """Adds some variables to every template context."""
    context = {}
    context['DISPLAY_TECH_SCORES'] = settings.DISPLAY_TECH_SCORES_IN_VIEW
    return context
