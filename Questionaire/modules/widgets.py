from PageDisplay.widgets import BaseModuleWidget

from Questionaire.models import Inquiry


class TechScoreWidget(BaseModuleWidget):
    template_name = "inquiry_pages/inquiry_snippets/snippet_tech_group_info.html"

    def get_context(self, request=None):
        context = super(TechScoreWidget, self).get_context(request)
        context['technology'] = self.model.technology
        if request:
            try:
                inquiry_id = context['inquiry'] = request.session.get('inquiry_id', None)
                if inquiry_id:
                    context['inquiry'] = Inquiry.objects.get(id=inquiry_id)
            except Inquiry.DoesNotExist:
                pass

        return context
