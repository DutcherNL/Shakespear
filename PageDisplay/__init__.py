from django.urls import reverse


def reverse_ns(request, url, kwargs):
    """ Reverses a url while keeping namespace contents """
    namespace = request.resolver_match.namespace
    if len(namespace) > 0:
        url = namespace + ":" + url
    return reverse(url, kwargs=kwargs)
