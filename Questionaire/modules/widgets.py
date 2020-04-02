from PageDisplay.module_widgets import BaseModuleWidget

from Questionaire.models import Inquirer


class TechScoreWidget(BaseModuleWidget):
    template_name = "inquiry/modules/module_tech_score.html"

    def get_context_data(self, request=None, **kwargs):
        context = super(TechScoreWidget, self).get_context_data(request)
        context['technology'] = self.model.technology
        context['inquiry'] = None
        if request:
            try:
                inquirer_id = request.session.get('inquirer_id', None)
                if inquirer_id:
                    context['inquiry'] = Inquirer.objects.get(id=inquirer_id).active_inquiry
            except Inquirer.DoesNotExist:
                pass

        return context
