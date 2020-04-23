from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from Questionaire.models import Technology
from PageDisplay.models import Page
from PageDisplay.sites import PageSite


class TechPageSite(PageSite):
    """ A custom site for the page display """
    can_be_edited = False
    site_context_fields = ['technology']
    use_page_keys = False
    namespace = "technologies"
    extends_template = "base_public.html"
    view_requires_login = False

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.technology = get_object_or_404(Technology, slug=kwargs['slug'])
        try:
            view_obj.page = view_obj.technology.information_page
        except Page.DoesNotExist:
            raise HttpResponseNotFound("Technology does not contain an information page")

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'slug': view_obj.technology.slug,
        }


tech_page_site = TechPageSite()
