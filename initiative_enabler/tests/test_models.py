import warnings
import datetime
from django.test import TestCase
from django.utils import timezone

from Questionaire.models import *
from initiative_enabler.models import *
from . import *


class CollectiveModelTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_tech_scores(self)
        set_up_tech_collective(self)

    def test_interested_inquirers(self):
        """ Tests that the interested inquiries method returns the correct result
         Assumption: if the correct number of instances is returned, so are the correct instances """
        self.assertEqual(self.c_1.get_interested_inquirers().count(), 2)
        interest = generate_interest_in_tech_collective(self.c_1)
        self.assertEqual(self.c_1.get_interested_inquirers().count(), 3)
        interest.is_interested = False
        interest.save()
        self.assertEqual(self.c_1.get_interested_inquirers().count(), 2)

        # Test that it excludes the target given
        interest = generate_interest_in_tech_collective(self.c_1)
        self.assertEqual(self.c_1.get_interested_inquirers(current_inquirer=interest).count(), 2)

    def test_collective_uninvited_inquirers(self):
        """ Test several methods in the collective related to rsvps """
        active_collective = InitiatedCollective.objects.create(
            tech_collective=self.c_2,
            inquirer=Inquirer.objects.create(),
        )

        # It defaults to 1 (1 who is interested, another who is not)
        self.assertEqual(active_collective.get_uninvited_inquirers().count(), 1)

        tech_interest = generate_interest_in_tech_collective(self.c_2)
        self.assertEqual(active_collective.get_uninvited_inquirers().count(), 2)

        CollectiveRSVP.objects.create(
            collective=active_collective,
            inquirer=tech_interest.inquirer,
        )
        self.assertEqual(active_collective.get_uninvited_inquirers().count(), 1)

        # Ensure that interest does not include the owner
        tech_interest = generate_interest_in_tech_collective(self.c_2)
        active_collective = InitiatedCollective.objects.create(
            tech_collective=self.c_2,
            inquirer=tech_interest.inquirer,
        )
        # 1 default + 1 created earlier + 0 for owner
        self.assertEqual(active_collective.get_uninvited_inquirers().count(), 2)

    def test_non_responded_rsvps(self):
        active_collective = InitiatedCollective.objects.create(
            tech_collective=self.c_1,
            inquirer=Inquirer.objects.create(),
        )

        # Create a response, this should be excluded from the uninvited inquiries
        CollectiveRSVP.objects.create(
            inquirer=Inquirer.objects.create(),
            collective=active_collective,
            activated=False
        )
        CollectiveRSVP.objects.create(
            inquirer=Inquirer.objects.create(),
            collective=active_collective,
            activated=False
        )
        self.assertEqual(active_collective.open_rsvps().count(), 2)
        CollectiveRSVP.objects.create(
            inquirer=Inquirer.objects.create(),
            collective=active_collective,
            activated=True
        )
        self.assertEqual(active_collective.open_rsvps().count(), 2)


class RsvpModelTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_rsvp(self)

    def test_rsvp_save_actions(self):
        self.assertFalse(self.rsvp.activated)
        self.assertIsNone(self.rsvp.activated_on)
        self.assertIsNotNone(self.rsvp.created_on)
        self.assertIsNotNone(self.rsvp.last_send_on)
        self.assertIsNotNone(self.rsvp.url_code)

        # Ensure that the activated timestamp is set when activated is set to True
        cur_time = timezone.now()
        self.rsvp.activated = True
        self.rsvp.save()
        self.assertGreaterEqual(self.rsvp.activated_on, cur_time)

        # Test the expire property
        self.assertFalse(self.rsvp.is_expired)
        self.rsvp.last_send_on -= datetime.timedelta(days=7)
        self.rsvp.save()
        self.assertTrue(self.rsvp.is_expired)





