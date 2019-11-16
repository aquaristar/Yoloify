import random
import os
import factory
from django.core.files import File
from yoloify.signup.factories import UserFactory
from yoloify.pinboard.models import Goal, Pin

TEST_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static/img/yoloify.png'))


class GoalFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Goal

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: 'test-goal{0}'.format(n))
    description = 'This is a test goal'
    pin_type = random.choice(['location', 'goal'])
    image = factory.LazyAttribute(lambda t: File(open(TEST_IMAGE)))


class PinFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Pin

    goal = factory.SubFactory(GoalFactory)
    user = factory.SubFactory(UserFactory)
