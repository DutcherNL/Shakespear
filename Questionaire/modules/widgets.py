from PageDisplay.widgets import BaseModuleWidget

from Questionaire.models import Inquiry


class TechScoreWidget(BaseModuleWidget):
    template_name = "pagedisplay/modules/module_tech_score.html"

    def get_context(self, request=None, **kwargs):
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
