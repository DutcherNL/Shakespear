import re

from Questionaire.models import InquiryQuestionAnswer, Score

# Assert that InquiryQuestionAnswer has the attribute get_readable_answer because dependency
assert hasattr(InquiryQuestionAnswer, 'get_readable_answer')


def format_from_database(text, inquiry=None):
    """ Formats the given text with information from the database

    :param text: The text that needs to be formatted.
    :param inquiry: The inquiry that it needs to apply on
    :return:
    """
    # Analyse the code source to determine where the source needs to be obtained
    # Find all text within brackets
    keys = re.findall("(?<!/)\{(.*?)(?<!/)\}", text)
    # Because of regex containing possible {} the regex tries to avoid /{ and /} markers in the query

    format_dict = {}

    for key in keys:
        if key is None:
            continue

        try:
            if key.startswith('q_'):
                q_name = key[2:]
                retrieve_code = False
                regex = None

                if key.endswith('__code'):
                    # Check if the code is requested
                    q_name = q_name[:-6]
                    retrieve_code = True
                elif '__regex=' in key:
                    [q_name, regex] = q_name.split('__regex=', 1)
                    short_question_name = q_name+'__regex'
                    text = text.replace(key, short_question_name)
                    key = short_question_name
                    q_name = q_name

                    # Regex could contain '/{' and '/}' chars, those need to be replaced
                    regex = regex.replace('/{', '{')
                    regex = regex.replace('/}', '}')

                iqa_obj = InquiryQuestionAnswer.objects.get(question__name=q_name, inquiry=inquiry)
                if len(iqa_obj.answer) > 0:
                    result = iqa_obj.get_readable_answer(with_answer_code=retrieve_code)
                    if regex:
                        result = re.search(regex, result)
                        if result:
                            result = result.group()
                        else:
                            result = ""
                    format_dict[key] = result
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
