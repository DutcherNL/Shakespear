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


class CollectiveRestrictionTestCase(TestCase):

    def setUp(self):
        set_up_tech_collective(self)
        set_up_restrictions(self)

    def test_question_restriction_values(self):
        self.assertTrue(self.rest_1.has_working_restriction(self.inquirer_1))
        self.assertFalse(self.rest_1.has_working_restriction(self.inquirer_answerless))

        rest_value = self.rest_1.generate_collective_data(self.inquirer_1)
        # It returns a list of collective data instances
        self.assertEqual(len(rest_value), 1)
        rest_value = rest_value[0]
        self.assertEqual(rest_value.value, '1234')
        self.assertEqual(rest_value.restriction_id, self.rest_1.id)

        rest_value = self.rest_1.generate_interest_data(self.inquirer_1)
        self.assertEqual(rest_value.value, '1234')
        self.assertEqual(rest_value.restriction_id, self.rest_1.id)

    def test_collection_creation(self):
        collective = InitiatedCollective.objects.create(
            tech_collective=self.c_1,
            inquirer=self.inquirer_1,
        )
        collective.set_restriction_values(self.inquirer_1)
        collective.refresh_from_db()

        self.assertEqual(collective.restriction_scopes.count(), 1)
        res_scope = collective.restriction_scopes.first()
        self.assertEqual(res_scope.restriction_id, self.rest_1.id)
        self.assertEqual(res_scope.value, '1234')

        # Restriction value can copy from other inquirers as well (just because)
        collective.set_restriction_values(inquirer=self.inquirer_2)
        self.assertEqual(collective.restriction_scopes.count(), 2)
        res_scope = collective.restriction_scopes.last()
        self.assertEqual(res_scope.restriction_id, self.rest_1.id)
        self.assertEqual(res_scope.value, 'OneTwo')

    def test_interest_creation(self):
        interest = TechCollectiveInterest.objects.create(
            tech_collective=self.c_1,
            inquirer=self.inquirer_1,
        )

        # Set restriction values defaults to the set inquirer
        interest.set_restriction_values()
        self.assertEqual(interest.restriction_scopes.count(), 1)
        res_scope = interest.restriction_scopes.last()
        self.assertEqual(res_scope.restriction_id, self.rest_1.id)
        self.assertEqual(res_scope.value, '1234')

        # Restriction value can copy from other inquirers as well (just because)
        interest.set_restriction_values(inquirer=self.inquirer_2)
        self.assertEqual(interest.restriction_scopes.count(), 2)
        res_scope = interest.restriction_scopes.last()
        self.assertEqual(res_scope.restriction_id, self.rest_1.id)
        self.assertEqual(res_scope.value, 'OneTwo')

    def test_restricted_tech_collective_interest(self):
        # The tech collective contains a restriction, thus check for interest with the same value for the restriction
        # as the inquirer. This is initially 0
        self.assertEqual(self.c_1.get_interested_inquirers(current_inquirer=self.inquirer_1).count(), 0)

        # Generate a new interest (without restriction values)
        interest = generate_interest_in_tech_collective(self.c_1)
        self.assertEqual(self.c_1.get_interested_inquirers(current_inquirer=self.inquirer_1).count(), 0)

        # Set the restriction value to a similar one as the user creaets
        interest.restriction_scopes.add(
            RestrictionValue.objects.get(
                restriction=self.rest_1,
                value='1234'
            )
        )
        self.assertEqual(self.c_1.get_interested_inquirers(current_inquirer=self.inquirer_1).count(), 1)

        # Ensure that there are no conflicts when there are multiple interests within the same restriction
        interest.restriction_scopes.add(
            RestrictionValue.objects.create(
                restriction=self.rest_1,
                value='8484'
            )
        )
        self.assertEqual(self.c_1.get_interested_inquirers(current_inquirer=self.inquirer_1).count(), 1)

    def test_restricted_collective_interest(self):
        collective = InitiatedCollective.objects.create(
            tech_collective=self.c_1,
            inquirer=Inquirer.objects.create(),
        )
        collective.restriction_scopes.add(
            RestrictionValue.objects.create(
                restriction=self.rest_1,
                value='test_value'
            )
        )
        # There is no interest in this collective adhering the restriction
        self.assertEqual(collective.get_uninvited_inquirers().count(), 0)

        # Generate a new interest (without restriction values)
        interest = generate_interest_in_tech_collective(self.c_1)
        self.assertEqual(collective.get_uninvited_inquirers().count(), 0)

        # Set the restriction value to a similar one as the user creaets
        interest.restriction_scopes.add(
            RestrictionValue.objects.get(
                restriction=self.rest_1,
                value='test_value'
            )
        )
        self.assertEqual(collective.get_uninvited_inquirers().count(), 1)
