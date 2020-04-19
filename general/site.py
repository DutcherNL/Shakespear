from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from general.models import BasePageURL
from PageDisplay.models import Page
from PageDisplay.sites import PageSite


class GeneralPagesSite(PageSite):
    """ A custom site for the page display """

    name = 'general_pages'
    use_page_keys = False
    view_requires_login = False
    extends_template = "base_public.html"

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.url_link = get_object_or_404(BasePageURL, slug=kwargs['slug'])
        view_obj.page = view_obj.url_link.page

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'slug': view_obj.url_link.slug,
        }


page_site = GeneralPagesSite()
