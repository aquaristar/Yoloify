from django.test import TestCase
from factories import GoalFactory, PinFactory
from .models import Goal, Pin


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class GoalTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.goal = GoalFactory.create()

    @classmethod
    def tearDownClass(cls):
        cls.goal.delete()

    def test_goal_creation(self):
        self.assertEqual(Goal.objects.count(), 1)
        self.assertEqual(Pin.objects.count(), 1)

    def test_is_reposted_by(self):
        self.assertEqual(self.goal.is_reposted_by(self.goal.user), False)


class PinTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin = PinFactory.build()
        cls.liked = True
        cls.completed = True
        cls.pin.create()

    @classmethod
    def tearDownClass(cls):
        cls.pin.delete()

    def test_pin_creation(self):
        self.assertEqual(Pin.objects.coun(), 1)

    def test_pin_deletion(self):
        self.assertEqual(Pin.objects.count(), 0)

    def test_pin_like(self):
        self.liked = True
        self.assertEqual(2, 4)

    def test_pin_unlike(self):
        self.assertEqual(2, 4)

    def test_pin_bookmark(self):
        self.assertEqual(2, 5)

    def test_pin_unbookmark(self):
        self.assertEqual(2, 5)

    def test_pin_complete(self):
        self.assertEqual(4, 5)

    def test_pin_uncomplete(self):
        self.assertEqual(4, 5)

    def test_is_repin_property(self):
        self.assertEqual(3, 5)

    def test_slug_title_property(self):
        self.assertEqual(3, 5)

    def test_is_reposted_by_method(self):
        self.assertEqual(3, 5)

    def test_pin_count(self):
        self.assertEqual(3, 5)

    def test_complete_count(self):
        self.assertEqual(2, 5)
