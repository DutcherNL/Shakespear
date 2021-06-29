import re
import datetime
from django.db import models
from django.utils.crypto import get_random_string
from django.shortcuts import reverse
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from initiative_enabler.postalcode_processors import get_range
from local_data_storage.models import DataTable, DataColumn
from Questionaire.models import Inquiry, Inquirer, InquiryQuestionAnswer, Score, Technology, Question
from reports.models import Report


__all__ = ['TechImprovement', 'TechCollective', 'InitiatedCollective', 'CollectiveRSVP', 'CollectiveApprovalResponse',
           'CollectiveDeniedResponse', 'CollectiveRSVPInterest', 'TechCollectiveInterest',
           'CollectiveRestriction', 'CollectiveQuestionRestriction', 'RestrictionValue',
           'InquirerDoesNotContainRestrictionValue', 'RestrictionRangeAdjustment',
           'RestrictionModifierDataTable', 'RestrictionModifierRange']


class TechImprovement(models.Model):
    """ Cotais some basic information regardig how to improve the technology in ones home. """
    technology = models.OneToOneField(Technology, on_delete=models.CASCADE)
    instructions_file = models.FileField(blank=True, null=True,
                   validators=[FileExtensionValidator(['pdf'])])
    instructions_file_name = models.CharField(max_length=32, blank=True, null=True)
    instructions_report = models.ForeignKey(Report, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"Tech Improvement guide for {self.technology}"

    def save(self, **kwargs):
        if self.instructions_file:
            if self.instructions_file_name is None or self.instructions_file_name == "":
                self.instructions_file_name = self.instructions_file.file.name

        return super(TechImprovement, self).save(**kwargs)

    @property
    def has_instructions_file(self):
        return self.instructions_file or self.instructions_report


class TechCollective(models.Model):
    """ A class describing a local possible collective to locally improve a technology """
    technology = models.OneToOneField(Technology, on_delete=models.PROTECT)
    description = models.CharField(max_length=512)
    instructions_file = models.FileField(blank=True, null=True,
                                         validators=[FileExtensionValidator(['pdf'])])
    instructions_report = models.ForeignKey(Report, on_delete=models.SET_NULL, blank=True, null=True)

    restrictions = models.ManyToManyField('CollectiveRestriction', through='RestrictionLink', blank=True)

    def get_interested_inquirers(self, current_inquirer=None, current_collective=None):
        """
        Retrusn a queryset of the currently interested inquirers
        :param current_inquirer: Optional: The current inquirer (this will be excluded in the list)
        :param current_collective: Optional: An initiated collective. Uses the Restricted values associated otherwise
        it uses the restricted values of the current_inquirer
        :return:
        """
        inquirers = Inquirer.objects.all()

        # Exclude the current inquirer
        if current_inquirer:
            inquirers = inquirers.exclude(id=current_inquirer.id)

        # Filter on those who have an interest in this tec
        inquirers = inquirers.filter(
            techcollectiveinterest__is_interested=True,
            techcollectiveinterest__tech_collective_id=self.id,
        )

        # Now it's needed to filter for the restriction values. If an initiated collective is given. Use the ones
        # on that instance. Otherwise obtain it through the current inquirer
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
                for restriction_link in self.restrictionlink_set.all():
                    if current_inquirer is None:
                        # There is no current inquirer given, so also no restriction value
                        raise InquirerDoesNotContainRestrictionValue(restriction=restriction_link.restriction)

                    scope = restriction_link.generate_collective_data(current_inquirer)
                    # filter for the scope if it is a single value, otherwise it's an iterable so treat it as such
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
                # This error can also be raised through any of the restriction links, hence the catch
                return inquirers.none()

        return inquirers

    def __str__(self):
        return f"Collective instructions for {self.technology}"

    @property
    def has_instructions_file(self):
        return self.instructions_file or self.instructions_report


class InquirerDoesNotContainRestrictionValue(Exception):
    """ An exception for when a value of an inquirer is attempt to retrieve, but was unable to """

    def __init__(self, restriction, message=None):
        self.message = message or f"Inquirer can not yield a value for restriction {restriction}"
        super().__init__(self.message)


class RestrictionRangeAdjustment(models.Model):
    """ Adjust a given input value to a range of values. Ideal for selecting e.g. postcodes in a certain range
    for example 4120 with range 4 yields a list of 4116 to 4124
    """
    min = models.CharField(max_length=24, default=1000)
    range = models.IntegerField(default=1)
    max = models.CharField(max_length=24, default=9999)
    type_choices = (
        ('NUM', 'Normal numeric number'),
        ('CMX', 'Complex value consisting of numbers and letters')
    )
    type = models.CharField(max_length=3, choices=type_choices, default='NUM')

    def get_range(self, input_value):
        if self.type == 'NUM':
            base_int = int(input_value)
            return list(range(
                max(int(self.min), base_int - self.range),
                min(int(self.max), base_int + self.range)
            ))
        elif self.type == 'CMX':
            return get_range(input_value, self.range, min_value=self.min, max_value=self.max)

    def clean(self):
        if self.type == 'num':
            # The type is a number, ensure the min and max are too
            try:
                float(self.min)
            except ValueError:
                raise ValidationError({'min': 'Minimum value must be a numeric entry.'})
            try:
                float(self.max)
            except ValueError:
                raise ValidationError({'max': 'Minimum value must be a numeric entry.'})

    def get_range_as_string(self, input_value):
        base_int = int(input_value)
        min_y = self.min
        range_y = self.range
        max_y = self.max
        return f"{max(int(self.min), base_int - self.range)} t/m {min(int(self.max), base_int + self.range)}"

    def __str__(self):
        return f"Range {self.type}: {self.range}"


class RestrictionLink(models.Model):
    collective = models.ForeignKey('TechCollective', on_delete=models.CASCADE)
    restriction = models.ForeignKey('CollectiveRestriction', on_delete=models.CASCADE)
    modifier = models.ForeignKey('RestrictionModifierBase', on_delete=models.SET_NULL, null=True, blank=True)
    range_adjustment = models.ForeignKey(RestrictionRangeAdjustment, on_delete=models.SET_NULL, null=True, blank=True)

    def get_collective_scope(self, inquirer, as_display_string=False):
        """ Returns a list of string based requirement values """
        value = self.restriction.get_as_child().get_collective_restriction_value(inquirer)
        if value is None:
            raise InquirerDoesNotContainRestrictionValue(self)

        if self.modifier:
            if self.modifier.get_as_child().can_modify(value):
                if as_display_string:
                    return [self.modifier.get_modified_as_string(value)]
                else:
                    return self.modifier.get_modified_values(value)

        if self.range_adjustment:
            if as_display_string:
                # Ensure it is a list otherwise it will split the string in characters later on
                return [self.range_adjustment.get_range_as_string(value)]
            else:
                return self.range_adjustment.get_range(value)
        else:
            return [value]

    def generate_collective_data(self, inquirer):
        """ Generates the data on the initiated collective that ensures the scope """
        answers = self.get_collective_scope(inquirer)

        restr_values = []
        for answer in answers:
            restr_values.append(RestrictionValue.objects.get_or_create(restriction=self.restriction, value=answer)[0])
        return restr_values

    @property
    def public_name(self):
        return self.restriction.public_name


class RestrictionModifierBase(models.Model):
    """ Base class for modifiers to adjuts the range of a restriction """

    def get_as_child(self):
        """ Returns the child object of this class"""
        # Loop over all children
        for child in self.__class__.__subclasses__():
            # If the child object exists
            if child.objects.filter(id=self.id).exists():
                return child.objects.get(id=self.id).get_as_child()
        return self

    def can_modify(self, input_value):
        raise NotImplementedError

    def get_modified_values(self, input_value):
        return self.get_as_child()._get_modified_values(input_value)

    def _get_modified_values(self, input_value):
        raise NotImplementedError()

    def get_modified_as_string(self, input_value):
        """ Returns the range a readable string to trim communication size """
        return self.get_as_child()._get_modified_as_string(input_value)

    def _get_modified_as_string(self, input_value):
        raise NotImplementedError()


class RestrictionModifierDataTable(RestrictionModifierBase):
    data_table = models.ForeignKey(DataTable, on_delete=models.CASCADE)
    data_column = models.ForeignKey(DataColumn, on_delete=models.PROTECT, related_name='restriction_modifier_data_set')
    text_column = models.ForeignKey(DataColumn, on_delete=models.PROTECT, related_name='restriction_modifier_text_set', null=True, blank=True)

    def can_modify(self, input_value):
        print(f"INPUT {input_value}")
        data = self.retrieve_entry_value(input_value, self.data_column)
        if data is None:
            # There is no data stored for this input_value so return false
            return False

        return True

    def _get_modified_values(self, input_value):
        """ Retrieves, if present, the defined value from the datatable"""
        range_values = self.retrieve_entry_value(input_value, self.data_column)

        if range_values:
            range_values = range_values.split(',')
            range_values = [i.strip() for i in range_values]
            return range_values
        else:
            return input_value

    def retrieve_entry_value(self, input_value, data_column):
        """ Retrieves the data from the datatable with the given input value and the data of the defined column.
         Returns None if no entry was found. """
        if not self.data_table.is_active:
            # if table is not active, return the value of input_value
            return None

        range_entry = self.data_table.get_data_table_entries().filter(
            **{
                self.data_table.db_key_column_name: input_value
            }
        ).first()

        if range_entry is None:
            return None

        return getattr(range_entry, data_column.db_column_name, None)

    def _get_modified_as_string(self, input_value):
        readable_range = None
        if self.text_column:
            readable_range = self.retrieve_entry_value(input_value, self.text_column)
        if readable_range is None or readable_range == "":
            readable_range = self.retrieve_entry_value(input_value, self.data_column)
        return str(readable_range)


class RestrictionModifierRange(RestrictionModifierBase):
    """ Modifies the restriction in accordance to a computed range of values """
    min = models.CharField(max_length=24, default=1000)
    range = models.IntegerField(default=1)
    max = models.CharField(max_length=24, default=9999)
    type_choices = (
        ('NUM', 'Normal numeric number'),
        ('CMX', 'Complex value consisting of numbers and letters')
    )
    type = models.CharField(max_length=3, choices=type_choices, default='NUM')

    def can_modify(self, input_value):
        # Check if the value is within the scope
        if input_value < self.min or input_value > self.max:
            return False
        else:
            return True

    def _get_modified_values(self, input_value):
        if self.type == 'NUM':
            base_int = int(input_value)
            return list(range(
                max(int(self.min), base_int - self.range),
                min(int(self.max), base_int + self.range)
            ))
        elif self.type == 'CMX':
            return get_range(input_value, self.range, min_value=self.min, max_value=self.max)

    def clean(self):
        if self.type == 'num':
            # The type is a number, ensure the min and max are too
            try:
                float(self.min)
            except ValueError:
                raise ValidationError({'min': 'Minimum value must be a numeric entry.'})
            try:
                float(self.max)
            except ValueError:
                raise ValidationError({'max': 'Minimum value must be a numeric entry.'})

    def _get_modified_as_string(self, input_value):
        if self.type == 'NUM':
            base_int = int(input_value)
            return f"{max(int(self.min), base_int - self.range)} t/m {min(int(self.max), base_int + self.range)}"
        elif self.type == 'CMX':
            values = get_range(input_value, self.range, min_value=self.min, max_value=self.max)
            return f"{values[0]} t/m {values[len(values)-1]}"

    def __str__(self):
        return f"Range {self.type}: {self.range}"


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

    def get_base_collective_value(self):
        raise NotImplementedError("This method should not be called in this class. Use .get_as_child() first to "
                                  "get the correct class.")

    def get_collective_restriction_value(self, inquirer):
        """
        Returns the collective restriction value.
        Raises InquirerDoesNotContainRestrictionValue if none can be found
        :param inquirer: the inquirer through which the value is obtained
        :return: A single string representing the value of the restriction
        """""
        value = self.get_base_collective_value(inquirer)
        if value is None:
            raise InquirerDoesNotContainRestrictionValue(self)

        return value

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

    def __str__(self):
        return self.name


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

    def get_base_collective_value(self, inquirer):
        return self.get_question_answer(inquirer)

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

    def __str__(self):
        return self.value


class InitiatedCollective(models.Model):
    """ The collective initiated by a user """
    tech_collective = models.ForeignKey(TechCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=True)

    message = models.TextField(max_length=500, verbose_name="Uitnodigings bericht")
    restriction_scopes = models.ManyToManyField(RestrictionValue)

    name = models.CharField(default="", max_length=128, verbose_name="Naam")
    address = models.CharField(default="", max_length=128, verbose_name="Adres")
    phone_number = models.CharField(max_length=15, verbose_name="Telefoonnummer")

    def clean(self):
        super(InitiatedCollective, self).clean()

    def set_restriction_values(self, inquirer: Inquirer = None):
        """
        Sets the restriction values according to the restrictions for the given inquirer. Defaults to the stored
        inquirer if none
        :param inquirer: The inquirer object. If None uses the instance inquirer
        """
        inquirer = inquirer or self.inquirer

        for restriction in self.tech_collective.restrictionlink_set.all():
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
                self.url_code = self.generate_url_code()
                if not CollectiveRSVP.objects.filter(url_code=self.url_code).exists():
                    return super(CollectiveRSVP, self).save(**kwargs)
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
    address = models.CharField(max_length=128, null=True, blank=True)
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
    last_updated = models.DateTimeField(auto_now=True)

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
            data = restriction.generate_interest_data(inquirer)
            # Determine whether it is a single restriciton value or a list/queryset of restriction values
            if isinstance(data, RestrictionValue):
                self.restriction_scopes.add(data)
            else:
                for value_instance in data:
                    self.restriction_scopes.add(value_instance)

    def __str__(self):
        return f"TechCollectiveInterest {self.tech_collective.technology.name}: {self.inquirer.id} {self.is_interested}"