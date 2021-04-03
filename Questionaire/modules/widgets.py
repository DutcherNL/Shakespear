from django.forms import Form

from PageDisplay.module_widgets import BaseModuleWidget

from Questionaire.models import Inquirer
from Questionaire.fields import QuestionFieldFactory
from Questionaire.utils import get_inquiry_from_request


class QuestionWidget(BaseModuleWidget):
    template_name = "inquiry/modules/module_question.html"
    use_from_context = ['inquirer', 'questionaire_form']

    def get_context_data(self, request=None, **kwargs):
        inquirer = kwargs.get('inquirer', None)
        questionaire_form = kwargs.get('questionaire_form', None)

        if inquirer:
            inquiry = inquirer.active_inquiry
        else:
            inquiry = None

        if questionaire_form:
            try:
                question_name = self.model.question.name
                field = questionaire_form[question_name]
            except KeyError:
                field = None
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
    use_from_context = ['inquiry']

    def get_context_data(self, request=None, inquiry=None, **kwargs):
        context = super(TechScoreWidget, self).get_context_data(request)
        context['technology'] = self.model.technology
        context['inquiry'] = inquiry or get_inquiry_from_request(request)

        return context
