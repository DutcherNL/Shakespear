from PageDisplay.models import VerticalModuleContainer


class A4_PageContainer(VerticalModuleContainer):
    def get_context_data(self, **kwargs):
        context = super(A4_PageContainer, self).get_context_data(kwargs)

        return context