from django.core.management.base import BaseCommand, CommandError

from questionaire_mailing.models import TimedMailTask

class Command(BaseCommand):
    help = 'Constructs and sends automatic e-mails'

    def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--no-mail',
            help='Do not actually send the e-mails, but merely construct them',
        )

    def handle(self, *args, **options):
        for poll_id in options['poll_ids']:
            try:
                poll = Poll.objects.get(pk=poll_id)
            except Poll.DoesNotExist:
                raise CommandError('Poll "%s" does not exist' % poll_id)

            poll.opened = False
            poll.save()

            self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))