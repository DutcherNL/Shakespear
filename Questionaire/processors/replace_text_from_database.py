from Questionaire.models import InquiryQuestionAnswer, Score
from string import Formatter


def format_from_database(text, inquiry=None):
    """ Formats the given text with information from the database

    :param text: The text that needs to be formatted.
    :param inquiry: The inquiry that it needs to apply on
    :return:
    """
    # Analyse the code source to determine where the source needs to be obtained
    formatter = Formatter()
    iter_obj = formatter.parse(text)
    keys = []
    for literal, key, format, conversion in iter_obj:
        keys.append(key)

    format_dict = {}

    for key in keys:
        if key is None:
            continue

        try:
            if key.startswith('q_'):
                q_name = key[2:]
                retrieve_code = False
                if key.endswith('__code'):
                    # Check if the code is requested
                    q_name = q_name[:-6]
                    retrieve_code = True
                iqa_obj = InquiryQuestionAnswer.objects.get(question__name=q_name, inquiry=inquiry)
                if len(iqa_obj.answer) > 0:
                    format_dict[key] = iqa_obj.get_readable_answer(with_answer_code=retrieve_code)
                else:
                    format_dict[key] = ""
            elif key.startswith('v_'):
                score_obj = Score.objects.get(declaration__name=key[2:], inquiry=inquiry)
                format_dict[key] = score_obj.score

        except InquiryQuestionAnswer.DoesNotExist:
            print("{key} did not exist".format(key=key))
            format_dict[key] = ""
        except Score.DoesNotExist:
            format_dict[key] = ""

    return text.format(**format_dict)
