from django.shortcuts import get_object_or_404
from django.http import HttpResponseNotFound

from Questionaire.models import Technology
from PageDisplay.models import Page
from PageDisplay.sites import PageSite


class TechPageSite(PageSite):
    """ A custom site for the page display """

    use_page_keys = False

    def get_header_buttons(self, view_class):
        from django.urls import reverse_lazy
        buttons = super(TechPageSite, self).get_header_buttons(view_class)
        buttons['Tech overview page'] = reverse_lazy('setup:tech_list')
        return buttons

    @staticmethod
    def init_view_params(view_obj, **kwargs):
        """ A method that sets view specific parameters, triggered in each view upon dispatch
        This methoed can also check access by raising a 404Error or 403Error
        """
        view_obj.technology = get_object_or_404(Technology, id=kwargs['tech_id'])
        try:
            view_obj.page = view_obj.technology.information_page
        except Page.DoesNotExist:
            raise HttpResponseNotFound("Technology does not contain an information page")

        # TODO: Continue with uncoupling url reverse arguments

    @staticmethod
    def get_url_kwargs(view_obj):
        return {
            'tech_id': view_obj.technology.id
        }


page_site = TechPageSite()
