from PageDisplay.sites import PageSite


class TechPageSite(PageSite):
    """ A custom site for the page display """

    def get_header_buttons(self, view_class):
        from django.urls import reverse_lazy
        buttons = super(TechPageSite, self).get_header_buttons(view_class)
        buttons['Tech overview page'] = reverse_lazy('setup:tech_list')
        return buttons


page_site = TechPageSite()
