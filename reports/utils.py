from django.template import Context, Template, Engine

from Questionaire.models import Technology, Inquiry


def full_render_layout(layout_html, context):
    template = Template(layout_html)

    context = Context(context)
    result = template.render(context)

    return result


class TechListReportPageRetrieval:
    TECHS_ADVISED = 'reports.techs.advised'
    TECHS_DENIED = 'reports.techs.denied'
    TECHS_UNKNOWN = 'reports.techs.unknown'

    @classmethod
    def get_applicable_techs(cls, request, score_mode):
        """ Returns the applicable technologies for the given score_mode """
        inquiry = Inquiry.objects.get(id=request.session.get('inquiry_id', None))

        # Create lists of various technology states
        techs = []

        for tech in Technology.objects.filter(display_in_step_2_list=True):
            if hasattr(tech, 'techgroup'):
                tech = tech.techgroup

            if tech.get_score(inquiry) == score_mode:
                techs.append(tech)

        return techs

    @classmethod
    def get_iterable(cls, request, mode):
        if mode == cls.TECHS_ADVISED:
            return cls.get_applicable_techs(request, Technology.TECH_SUCCESS)
        elif mode == cls.TECHS_DENIED:
            return cls.get_applicable_techs(request, Technology.TECH_FAIL)
        elif mode == cls.TECHS_UNKNOWN:
            return cls.get_applicable_techs(request, Technology.TECH_UNKNOWN)
        else:
            raise KeyError("mode was not defined")