from django.core.management.base import BaseCommand, CommandError

from questionaire_mailing.models import TimedMailTask


class Command(BaseCommand):
    help = 'Constructs and sends automatic e-mails'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--no-mail',
            action='store_false',
            help='Do not actually send the e-mails, but merely construct them',
        )

    def handle(self, *args, **options):
        send_mail = options['no_mail']

        processed = 0

        for timed_task in TimedMailTask.objects.filter(active=True):
            processed += timed_task.generate_mail(send_mail=send_mail)