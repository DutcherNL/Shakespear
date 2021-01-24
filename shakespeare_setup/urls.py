import inspect
from importlib import import_module

from django.apps import apps
from django.urls import path, include

from shakespeare_setup.config import SetupConfig

# Get all packages


def get_all_configs():
    """ Returns a list of all setup configs used by this application"""
    configs = []
    print('get_configs')

    for app in apps.get_app_configs():
        try:
            module = import_module(f'{app.name}.setup.config')
        except ModuleNotFoundError:
            pass
        else:
            print(app)
            for name, cls in module.__dict__.items():
                if isinstance(cls, type):
                    # Get all subclasses of SetupConfig, but not accidental imported copies of SetupConfig
                    if issubclass(cls, SetupConfig) and cls != SetupConfig:
                        configs.append(cls())
    return configs


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
