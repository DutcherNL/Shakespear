from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.urls import reverse

from Questionaire.models import Inquirer


class PendingMailVerifyer(models.Model):
    inquirer = models.ForeignKey(Inquirer, on_delete=models.CASCADE)
    email = models.EmailField()
    code = models.CharField(max_length=60, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)
    processed_on = models.DateTimeField(blank=True, null=True)

    def save(self, **kwargs):
        if self.id is None:
            """ Ensure that this this the only active pending mail for this inquirer """
            PendingMailVerifyer.objects.filter(inquirer=self.inquirer).update(active=False)

        if self.code is None or self.code == "":
            while True:
                self.code = self.generate_code()
                if not PendingMailVerifyer.objects.filter(code=self.code).exists():
                    return super(PendingMailVerifyer, self).save(**kwargs)
        else:
            return super(PendingMailVerifyer, self).save(**kwargs)

    def generate_code(self):
        return get_random_string(length=40)

    def verify(self):
        """ Sets the pending email as activated email """
        self.inquirer.email = self.email
        self.inquirer.email_validated = True
        self.inquirer.save()
        self.is_verified = True
        self.processed = True
        self.processed_on = timezone.now()
        self.active = False
        self.save()

    def get_absolute_url(self):
        return reverse('inquirer_settings:validate_mail')+f'?code={self.code}&email={self.email}'

