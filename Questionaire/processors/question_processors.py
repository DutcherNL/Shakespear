
from django.db.models import IntegerField as IntegerDBField
from django.db.models import DecimalField as DecimalDBField
from django.db.models.functions import Cast


""" This file contains code that allows the question to find its related answer """

__all__ = ['get_answer_option_through_question', 'get_answer_option_from_answer']


def get_answer_option_from_answer(answer_obj):
    return get_answer_option_through_question(answer_obj.question, answer_obj.answer)


def get_answer_option_through_question(question, answer_value):
    # Import here to avoid circular imports
    from Questionaire.models import Question

    q_type = question.question_type

    if q_type == Question.TYPE_OPEN:
        # Text question
        return get_open_answer_option(question, answer_value)
    if q_type == Question.TYPE_INT:
        # Integer question
        return get_int_answer_option(question, answer_value)
    if q_type == Question.TYPE_DOUBLE:
        # Double question
        return get_double_answer_option(question, answer_value)
    if q_type == Question.TYPE_CHOICE:
        # Multiple choice question
        return get_choice_answer_option(question, answer_value)


def get_open_answer_option(question, answer_value):
    if answer_value is None:
        return None

    if answer_value == "":
        return None

    not_none_answer = question.answeroption_set.filter(answer="NotNone")

    if not_none_answer.exists():
        return not_none_answer.get()

    return None


def get_int_answer_option(question, answer_value):
    if answer_value is None:
        return None

    # Get all answer options
    options = question.answeroption_set.all()
    # Select the answer that closest approximates, but not exceeds the inserted value
    options = options.annotate(answer_int=Cast('answer', IntegerDBField()))
    options = options.filter(answer_int__lte=answer_value)
    return options.order_by('answer_int').last()


def get_double_answer_option(question, answer_value):
    if answer_value is None:
        return None

    # Get all answer options
    options = question.answeroption_set.all()
    # Select the answer that closest approximates, but not exceeds the inserted value
    options = options.annotate(answer_int=Cast('answer', DecimalDBField()))
    options = options.filter(answer_int__lte=answer_value)
    return options.order_by('answer_int').last()


def get_choice_answer_option(question, answer_value):
    # If no answer is given, return nothing, else, return the selected answer
    if answer_value is None or answer_value == '':
        return None
    else:
        return question.answeroption_set.get(value=int(answer_value))