from django.conf import settings


def get_absolute_url_path(path):
    """ 
    Returns an absolute version of the given url path
    :param path: The local path
    :return: A full url path that can be used anywhere (reports, mails etc)
    """""

    domain_name = settings.DOMAIN_NAME
    if not domain_name.startswith('http'):
        domain_name = 'https://'+domain_name
    print(domain_name)
    if domain_name.endswith('/'):
        domain_name = domain_name[:-1]

    if path.startswith('/'):
        path = path[1:]

    return f'{domain_name}/{path}'