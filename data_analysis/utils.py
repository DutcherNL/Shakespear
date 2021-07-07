from Questionaire.models import TechScoreLink, Inquiry


def get_total_tech_scores(technology, inquiries=None):
    """
    Returns a list of the number of approved, unknown and denied tech scores
    :param technology: The technology that requires the score
    :param inquiries: An optional queryset of the Inquiry instances
    :return: A list with three values: number of approved, number of unknown data and number of non-recommanded
    inquiries for this technology
    """
    if inquiries is None:
        # It could be that inquiries is an empty dataset, that is fine.
        inquiries = Inquiry.objects.all()

    num_inquiries = inquiries.count()
    approved_inquiries = inquiries
    denied_inquiries = inquiries
    score_links = technology.techscorelink_set.all()

    if score_links.count() == 0:
        if technology.get_as_techgroup is not None:
            # In case this is a tech group. Treat it by checking its sub technologies
            subtechs = technology.get_as_techgroup.sub_technologies.all()
            score_links = TechScoreLink.objects.filter(technology__in=subtechs)
        else:
            # There are no links and no tech groups. So nothing can be displayed
            return [0, 0, 0]

    for link in score_links:
        approved_inquiries = approved_inquiries.filter(
            score__declaration=link.score_declaration,
            score__score__gte=link.score_threshold_approve
        )
        denied_inquiries = denied_inquiries.filter(
            score__declaration=link.score_declaration,
            score__score__lte=link.score_threshold_deny
        )

    num_approved = approved_inquiries.count()
    num_denied = denied_inquiries.count()
    num_unknown = num_inquiries - num_approved - num_denied
    return [num_approved, num_unknown, num_denied]