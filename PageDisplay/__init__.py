from django.urls import reverse


def reverse_ns(request, url, kwargs):
    """ Reverses a url while keeping namespace contents """
    namespace = request.resolver_match.namespace
    if len(namespace) > 0:
        url = namespace + ":" + url
    return reverse(url, kwargs=kwargs)


def create_limited_copy(dictionary, *args):
    """ Creates a limited copy of the given dictionary containing the given arguments """
    new_dict = {}
    for arg in args:
        new_dict[arg] = dictionary.get(arg, None)
    return new_dict