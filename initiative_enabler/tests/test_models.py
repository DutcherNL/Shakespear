import warnings
from django.test import TestCase
from django.utils import timezone

from Questionaire.models import *
from initiative_enabler.models import *
from . import *


class CollectiveModelTestCase(TestCase):
    def setUp(self):
        # Set up the database
        set_up_questionaires(self)

    def test_similar_inquiries(self):
        """ Tests that the similar inquiries method works properly """
        tech_col_1 = TechCollective.objects.create(technology=self.t1, description="Tech_1")
        self.assertEqual(tech_col_1.get_similar_inquiries(self.inquiry).count(), 2)

        tech_col_1 = TechCollective.objects.create(technology=self.t2, description="Tech_2")
        self.assertEqual(tech_col_1.get_similar_inquiries(self.inquiry).count(), 1)

    def test_collective_rsvp_methods(self):
        """ Test several methods in the collective related to rsvps """
        tech_col_1 = TechCollective.objects.create(technology=self.t1, description="Tech_1")

        # Generate a new inquiry to test the rsvps with
        score_declaration = self.t1.score_declarations.first()
        inquiry = generate_inquiry_with_score(score_declaration, 10)

        active_collective = InitiatedCollective.objects.create(
            tech_collective=tech_col_1,
            inquirer=self.inquiry.inquirer)

        self.assertEqual(active_collective.get_uninvited_inquiries().count(), 3)

        # Create a response, this should be excluded from the uninvited inquiries
        rsvp = CollectiveRSVP.objects.create(inquirer=inquiry.inquirer, collective=active_collective)

        self.assertEqual(active_collective.get_uninvited_inquiries().count(), 2)
        self.assertEqual(active_collective.open_rsvps().count(), 1)
        rsvp.activated = True
        rsvp.save()
        self.assertEqual(active_collective.open_rsvps().count(), 0)


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
        warning_message = " Note: Because the expire property uses timezone.now() and a field with 'auto_add_now'" \
                          " testing is limited to only the presence, not the execution. Ensure yourself that it gives " \
                          " the correct output for given times. "
        warnings.warn(warning_message, UserWarning)
        self.assertFalse(self.rsvp.is_expired)




