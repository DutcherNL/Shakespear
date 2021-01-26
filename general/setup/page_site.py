from django.shortcuts import get_object_or_404

from general.models import BasePageURL
from PageDisplay.sites import PageSite


class GeneralSetupPageSite(PageSite):
    """ A custom site for the page display """

    namespace = 'pages'
    use_page_keys = False
    breadcrumb_trail_template = "general/setup/snippet_breadcrumb_trail_general_pages.html"
    site_context_fields = ['url_link']
    edit_requires_permissions = ['Questionaire.change_basepageurl']

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


general_page_site = GeneralSetupPageSite()