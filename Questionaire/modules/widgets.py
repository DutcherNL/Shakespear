from django.forms import Form

from PageDisplay.module_widgets import BaseModuleWidget

from Questionaire.models import Inquirer
from Questionaire.fields import QuestionFieldFactory


class QuestionWidget(BaseModuleWidget):
    template_name = "inquiry/modules/module_question.html"
    use_from_context = ['inquirer', 'inquiry_form']

    def get_context_data(self, request=None, inquirer=None, inquiry_form=None, **kwargs):
        if inquirer:
            inquiry = inquirer.active_inquiry
        else:
            inquiry = None

        if inquiry_form:
            field = inquiry_form[self.model.question.name]
        else:
            # The field is not in a form context (e.g. on an edit page)
            # create a simple form to contain the field in instead (this prevents any errors due to field rendering
            # without any form related attributes
            class SimpleMockForm(Form):
                field = QuestionFieldFactory.get_field_by_questionmodel(
                    question=self.model.question,
                    inquiry=inquiry,
                    required=self.model.required,
                )
            field = SimpleMockForm()['field']

        return super(QuestionWidget, self).get_context_data(
            request,
            field=field,
            **kwargs
        )


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
