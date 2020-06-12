import re
import datetime
from django.db import models, IntegrityError
from django.utils.crypto import get_random_string
from django.shortcuts import reverse
from django.utils import timezone
from django.core.validators import FileExtensionValidator

from Questionaire.models import Inquiry, Inquirer, InquiryQuestionAnswer, Score, Technology, Question


__all__ = ['TechCollective', 'InitiatedCollective', 'CollectiveRSVP', 'CollectiveApprovalResponse',
           'CollectiveDeniedResponse', 'CollectiveRSVPInterest', 'TechCollectiveInterest',
           'CollectiveRestriction', 'CollectiveQuestionRestriction', 'RestrictionValue']


class TechCollective(models.Model):
    """ A class describing a local possible collective to locally improve a technology """
    technology = models.OneToOneField(Technology, on_delete=models.PROTECT)
    description = models.CharField(max_length=512)
    instructions_file = models.FileField(blank=True, null=True,
                                         validators=[FileExtensionValidator(['pdf'])])

    restrictions = models.ManyToManyField('CollectiveRestriction', blank=True)

    def get_interested_inquirers(self, current_inquirer=None, current_collective=None):
        inquirers = Inquirer.objects.all()

        if current_inquirer:
            inquirers = inquirers.exclude(id=current_inquirer.id)

        inquirers = inquirers.filter(
            techcollectiveinterest__is_interested=True,
            techcollectiveinterest__tech_collective_id=self.id,
        )

        if current_collective:
            if self.restrictions.all():
                # If itself contains restrictions, filter for those restriction values
                inquirers = inquirers.filter(
                    techcollectiveinterest__restriction_scopes__in=current_collective.restriction_scopes.all()
                )
        else:
            # Interested inquirers should be based through the inquirer. However, when there is no restriction
            # this should not pose problems
            try:
                for restriction in self.restrictions.all():
                    if current_inquirer is None:
                        raise InquirerDoesNotContainRestrictionValue

                    scope = restriction.generate_collective_data(current_inquirer)
                    if isinstance(scope, RestrictionValue):
                        inquirers = inquirers.filter(
                            techcollectiveinterest__restriction_scopes=scope
                        )
                    else:
                        inquirers = inquirers.filter(
                            techcollectiveinterest__restriction_scopes__in=scope
                        )
            except InquirerDoesNotContainRestrictionValue:
                # The restriction value can not be obtained, so there are no matches
                return inquirers.none()

        return inquirers

    def __str__(self):
        return str(self.technology)


class InquirerDoesNotContainRestrictionValue(Exception):
    """ An exception for when a value of an inquirer is attempt to retrieve, but was unable to """

    def __init__(self, restriction, message=None):
        self.message = message or f"Inquirer can not yield a value for restriction {restriction}"
        super().__init__(self.message)


class CollectiveRestriction(models.Model):
    name = models.CharField(max_length=64)
    public_name = models.CharField(max_length=64)
    description = models.CharField(max_length=512)

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self

    def get_interested_inquirers(self, inquirer_queryset, current_inquirer=None, tech_collective=None):
        """ Returns all interested inquirers in the given inquirer_queryset
        :param inquirer_queryset: A queryset of allread limited inquirers
        :param current_inquirer: The current inquirer
        :param tech_collective: The tech collective this is part of
        """
        return inquirer_queryset

    def generate_collective_data(self, inquirer):
        """ Generates the data on the initiated collective that ensures the scope """
        answers = self.get_as_child().get_collective_scope(inquirer)
        restr_values = []
        for answer in answers:
            restr_values.append(RestrictionValue.objects.get_or_create(restriction=self, value=answer)[0])
        return restr_values

    def get_collective_scope(self, inquirer):
        """ Returns a list of string based requirement values """
        raise NotImplementedError("This method should not be called in this class. Use .get_as_child() first to "
                                  "get the correct class.")

    def generate_interest_data(self, inquirer):
        """ Generates the data on the collective interest that ensures the scope """
        # Activate the method as the child to ensure correct outcome
        return self.get_as_child().generate_interest_data(inquirer)

    def has_working_restriction(self, inquirer):
        """ Tests whether the inquirer contains the required type of value (regardless of the value)
        e.g. whether a certain question ahs been answered"""
        # Activate the method as the child to ensure correct outcome
        return self.get_as_child().has_working_restriction(inquirer)

    def get_value_form_class(self):
        """ Returns a form that allows retrieving this value manually in case it can not be found otherwise """
        raise NotImplementedError("This method should not be called in this class. Use .get_as_child() first to "
                                  "get the correct class.")


class CollectiveQuestionRestriction(CollectiveRestriction):
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    regex = models.CharField(max_length=128, blank=True, null=True)

    def get_question_answer(self, inquirer):
        """ Retrieves the regex adjusted answer in the questionaire for the given inquirer """
        # Get the answer
        answer = InquiryQuestionAnswer.objects.filter(
            question=self.question,
            inquiry__inquirer=inquirer,
        )
        if answer.exists():
            answer = answer.first().answer

            if self.regex:
                answer = re.search(self.regex, answer)
                if answer:
                    answer = answer.group()
            return answer
        else:
            return None

    def get_collective_scope(self, inquirer):
        answer = self.get_question_answer(inquirer)
        if answer is None:
            raise InquirerDoesNotContainRestrictionValue(self)

        return [answer]

    def generate_interest_data(self, inquirer, undo=False):
        """ Generates the data on the collective interest that ensures the scope """
        # Generates the related data in the interest model
        answer = self.get_question_answer(inquirer)
        return RestrictionValue.objects.get_or_create(restriction=self, value=answer)[0]

    def has_working_restriction(self, inquirer):
        """ Tests whether the inquirer contains the required type of value (regardless of the value)
        e.g. whether a certain question ahs been answered"""
        return self.get_question_answer(inquirer) is not None

    def get_value_form_class(self):
        """ Returns a form that allows updating this value if the answer is not given in the questionaire"""
        from initiative_enabler.forms import UpdateQuestionRestrictionForm
        return UpdateQuestionRestrictionForm


class RestrictionValue(models.Model):
    restriction = models.ForeignKey(CollectiveRestriction, on_delete=models.CASCADE)
    value = models.CharField(max_length=32)


class InitiatedCollective(models.Model):
    """ The collective initiated by a user """
    tech_collective = models.ForeignKey(TechCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=True)

    message = models.TextField(max_length=500)
    restriction_scopes = models.ManyToManyField(RestrictionValue)

    name = models.CharField(default="", max_length=128, verbose_name="Naam")
    address = models.CharField(default="", max_length=128, verbose_name="Adres")
    phone_number = models.CharField(max_length=15, verbose_name="Tel")

    def clean(self):
        super(InitiatedCollective, self).clean()

    def set_restriction_values(self, inquirer: Inquirer = None):
        """
        Sets the restriction values according to the restrictions for the given inquirer. Defaults to the stored
        inquirer if none
        :param inquirer: The inquirer object. If None uses the instance inquirer
        """
        inquirer = inquirer or self.inquirer

        for restriction in self.tech_collective.restrictions.all():
            data = restriction.generate_collective_data(inquirer)
            # Determine whether it is a single restriciton value or a list/queryset of restriction values
            if isinstance(data, RestrictionValue):
                self.restriction_scopes.add(data)
            else:
                for value_instance in data:
                    self.restriction_scopes.add(value_instance)

    def open_rsvps(self):
        return self.collectiversvp_set.filter(activated=False)

    def get_absolute_url(self):
        return reverse("collectives:actief_collectief_details", kwargs={
            'collective_id': self.id
        })

    def get_uninvited_inquirers(self):
        """
        Returns all inquirers who are interested and not yet invited to this collective
        :return:
        """
        inquirers = self.tech_collective.get_interested_inquirers(current_collective=self)
        inquirers = inquirers.exclude(initiatedcollective=self)
        inquirers = inquirers.exclude(collectiversvp__collective=self)
        return inquirers


class CollectiveRSVP(models.Model):
    """ The queried people and there responses """
    collective = models.ForeignKey(InitiatedCollective, on_delete=models.SET_NULL, null=True)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.CASCADE)
    url_code = models.SlugField(max_length=64, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_send_on = models.DateTimeField(default=timezone.now)
    activated = models.BooleanField(default=False)
    activated_on = models.DateTimeField(blank=True, null=True)

    @property
    def is_expired(self):
        return self.last_send_on + datetime.timedelta(days=7) <= timezone.now()

    def save(self, **kwargs):
        if self.activated and self.activated_on is None:
            self.activated_on = timezone.now()

        if self.url_code is None or self.url_code == "":
            while True:
                try:
                    self.url_code = self.generate_url_code()
                    return super(CollectiveRSVP, self).save(**kwargs)
                except IntegrityError:
                    pass
        else:
            return super(CollectiveRSVP, self).save(**kwargs)

    def generate_url_code(self):
        return get_random_string(length=40)

    def get_local_absolute_url(self):
        return reverse("collectives:rsvp", kwargs={
            'collective_id': self.collective.id
        })

    def get_absolute_url(self):
        return reverse("collectives:rsvp", kwargs={
            'rsvp_slug': self.url_code
        })

    def __str__(self):
        return f'{self.collective.id} - {self.inquirer.id}'


class CollectiveApprovalResponse(models.Model):
    """ The responsed i.e. approved RSVP's """
    collective = models.ForeignKey(InitiatedCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.SET_NULL, null=True)
    message = models.TextField(max_length=1200, blank=True, null=True, verbose_name="Bericht aan de initiatiefnemer")
    name = models.CharField(max_length=128)
    address = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=15)


class CollectiveDeniedResponse(models.Model):
    """ The responsed rsvp that was not accepted."""
    collective = models.ForeignKey(InitiatedCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.SET_NULL, null=True)


class CollectiveRSVPInterest(models.Model):
    """ A list of interested RSVP's who were once invited, but when redeeming their invitation arrived
    at a closed collective. It is used to automatically send invitations when reopening """
    collective = models.ForeignKey(InitiatedCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.CASCADE)
    timestamp_created = models.DateTimeField(auto_now_add=True)


class TechCollectiveInterest(models.Model):
    tech_collective = models.ForeignKey(TechCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.CASCADE)
    is_interested = models.BooleanField(default=False)

    restriction_scopes = models.ManyToManyField(RestrictionValue, blank=True)

    class Meta:
        unique_together = ['tech_collective', 'inquirer']

    def set_restriction_values(self, inquirer: Inquirer = None):
        """
        Sets the restriction values according to the restrictions for the given inquirer. Defaults to the stored
        inquirer if none
        :param inquirer: The inquirer object. If None uses the instance inquirer
        """
        inquirer = inquirer or self.inquirer
        for restriction in self.tech_collective.restrictions.all():
            data = restriction.generate_collective_data(inquirer)
            # Determine whether it is a single restriciton value or a list/queryset of restriction values
            if isinstance(data, RestrictionValue):
                self.restriction_scopes.add(data)
            else:
                for value_instance in data:
                    self.restriction_scopes.add(value_instance)
