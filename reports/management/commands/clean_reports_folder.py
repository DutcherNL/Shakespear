import os
import datetime


from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from reports.models import RenderedReport, Report


class Command(BaseCommand):
    help = 'Clean outdated PDF files from the created reports folder'

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--keep_unused',
            action='store_true',
            help='Prevents clearing small-time PDF files created in Setup',
        )
        parser.add_argument(
            '--keep_outdated',
            action='store_true',
            help='Prevents clearing outdated inquiry files',
        )
        parser.add_argument(
            '--keep_static',
            action='store_true',
            help='Prevents clearing of old static reports (except the newest version)',
        )

    def handle(self, *args, **options):
        # If not all maximum running tasks, activate a task in the queue
        if not options['keep_unused']:
            # Clear the contents of the onetime folder. This is used for pdf creation in the setup. For instance
            # on single page PDF's.

            dir = os.path.join(settings.REPORT_ROOT, 'onetime')
            num_deleted = 0
            for f in os.listdir(dir):
                os.remove(os.path.join(dir, f))
                num_deleted += 1
            print(f"Removed {num_deleted} onetime files")

        if not options['keep_outdated']:
            dif_days = 3
            threshold = timezone.now() - datetime.timedelta(days=dif_days)

            num_deleted = 0
            for report in RenderedReport.objects.filter(created_on__lte=threshold, report__is_static=False):
                report.delete()
                num_deleted += 1
            print(f"Removed {num_deleted} outdated files")

        if not options['keep_static']:
            # Clear old versions of static reports
            for report_group in Report.objects.filter(is_static=True):
                is_first = True
                for report in RenderedReport.objects.filter(report=report_group).order_by('created_on'):
                    if is_first:
                        is_first = False
                    else:
                        report.delete()
                        num_deleted += 1
            print(f"Removed {num_deleted} old static pdf-files")
