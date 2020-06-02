import re
import datetime
from django.db import models, IntegrityError
from django.utils.crypto import get_random_string
from django.shortcuts import reverse
from django.utils import timezone

from Questionaire.models import Inquiry, Inquirer, InquiryQuestionAnswer, Score, Technology, Question


__all__ = ['TechCollective', 'InitiatedCollective', 'CollectiveRSVP', 'CollectiveApprovalResponse',
           'CollectiveDeniedResponse', 'CollectiveRSVPInterest', 'TechCollectiveInterest']


class TechCollective(models.Model):
    """ A class describing a local possible collective to locally improve a technology """
    technology = models.OneToOneField(Technology, on_delete=models.PROTECT)
    description = models.CharField(max_length=512)

    def get_interested_inquirers(self, current_inquirer=None):
        inquirers = Inquirer.objects.all()

        if current_inquirer:
            inquirers = inquirers.exclude(id=current_inquirer.id)

        inquirers = inquirers.filter(
            techcollectiveinterest__is_interested=True,
            techcollectiveinterest__tech_collective_id=self.id
        )

        return inquirers

    def __str__(self):
        return str(self.technology)


class CollectiveFilter(models.Model):
    """ A filter that ensures one can query for all similar answers"""
    # Entry.objects.get(headline__contains='Lennon')
    collective = models.ForeignKey(TechCollective, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    regex = models.CharField(max_length=128, blank=True, null=True)

    def get_similar_inquiries(self, inquiry, inquiry_set=None):
        answer = InquiryQuestionAnswer.objects.filter(inquiry=inquiry, question=self.question)
        if answer.exists():
            # There should be only one answer, but just for safety, just retreive the first answer
            answer = answer.first().answer

            if self.regex:
                answer = re.search(self.regex, answer)
            if answer:
                answer = answer.group()

                if inquiry_set is None:
                    inquiry_set = Inquiry.objects.all()
                return inquiry_set.filter(inquiryquestionanswer__answer__icontains=answer)
        # No answer matching the query has been found, so return empty handed
        return None


class InitiatedCollective(models.Model):
    """ The collective initiated by a user """
    tech_collective = models.ForeignKey(TechCollective, on_delete=models.CASCADE)
    inquirer = models.ForeignKey(Inquirer, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=True)

    message = models.TextField(max_length=500)

    name = models.CharField(default="", max_length=128, verbose_name="Naam")
    address = models.CharField(default="", max_length=128, verbose_name="Adres")
    phone_number = models.CharField(max_length=15, verbose_name="Tel")

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
        inquirers = self.tech_collective.get_interested_inquirers(None)
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

    class Meta:
        unique_together = ['tech_collective', 'inquirer']
