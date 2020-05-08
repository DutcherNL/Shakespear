from django.forms import Form, CharField, ModelForm, ValidationError

from initiative_enabler.models import *


class StartCollectiveForm(ModelForm):
    uitnodiging = CharField()

    class Meta:
        model = InitiatedCollective
        fields = ["name", "host_address", "phone_number", "uitnodiging"]

    def __init__(self, inquirer, tech_collective, **kwargs):
        self.inquirer = inquirer
        self.tech_collective = tech_collective
        super(StartCollectiveForm, self).__init__(**kwargs)

    def save(self, commit=True):
        self.instance.inquirer = self.inquirer
        self.instance.tech_collective = self.tech_collective
        self.instance = super(StartCollectiveForm, self).save(commit=commit)

        inquiries = self.tech_collective.get_similar_inquiries(self.inquirer.active_inquiry)
        rsvp_targets = Inquirer.objects.filter(inquiry__in=inquiries).distinct().exclude(id=self.inquirer.id)

        for target in rsvp_targets:
            CollectiveRSVP.objects.create(collective=self.instance,
                                          inquirer=target)
            # TODO: Send mail accoriding to all RSVP objects
        return self.instance


class RSVPAgreeForm(ModelForm):
    class Meta:
        model = CollectiveApprovalResponse
        fields = ["name", "address", "phone_number", "message"]

    def __init__(self, rsvp, **kwargs):
        self.rsvp = rsvp
        super(RSVPAgreeForm, self).__init__(**kwargs)

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Dit verzoek is al reeds behandeld")

    def save(self, commit=True):
        self.instance.collective = self.rsvp.collective
        self.instance.inquirer = self.rsvp.inquirer
        self.instance = super(RSVPAgreeForm, self).save(commit=commit)

        self.rsvp.activated = True
        self.rsvp.save()
        return self.instance


class RSVPDisagreeForm(ModelForm):
    class Meta:
        model = CollectiveDeniedResponse
        fields = []

    def __init__(self, rsvp, **kwargs):
        self.rsvp = rsvp
        super(RSVPDisagreeForm, self).__init__(**kwargs)

    def clean(self):
        if self.rsvp.activated:
            raise ValidationError("Dit verzoek is al reeds behandeld")

    def save(self, commit=True):
        self.instance.collective = self.rsvp.collective
        self.instance.inquirer = self.rsvp.inquirer
        self.instance = super(RSVPDisagreeForm, self).save(commit=commit)

        self.rsvp.activated = True
        self.rsvp.save()
        return self.instance