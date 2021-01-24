from importlib import import_module

from django.apps import apps
from django.urls import path, include

from shakespeare_setup.config import get_all_configs


def get_setup_urls():
    """
    Go over all installed apps and look for the urls file in the setup folder.
    This way we can assign the relevant setup views and the like to the modules instead of dumping it through
    a chain of apps.

    :return:
    """
    urls = []

    for app in apps.get_app_configs():
        setup_urls_name = f'{app.name}.setup'
        try:
            module = import_module(setup_urls_name+'.urls')
        except ModuleNotFoundError:
            pass
        else:
            urls.append(
                path(f'{module.url_key}/', include(setup_urls_name+'.urls'))
            )

    # Try to load the setup config files
    for setup_config in get_all_configs():
        urls.append(path(f'{setup_config.url_keyword}/', setup_config.urls))

    return urls, 'setup', 'setup'
