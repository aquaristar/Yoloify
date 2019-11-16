import factory
from django.contrib.auth.models import User
from yoloify.signup.models import Profile


class ProfileFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Profile

    username = factory.Sequence(lambda n: 'username{0}'.format(n))
    user = factory.SubFactory('yoloify.signup.factories.UserFactory', profile=None)
    is_signup_finished = True


class UserFactory(factory.DjangoModelFactory):
    FACTORY_FOR = User

    email = factory.Sequence(lambda n: 'test_{0}@email.com'.format(n))
    username = factory.Sequence(lambda n: 'username{0}'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'adm1n')
    is_active = True

    profile = factory.RelatedFactory(ProfileFactory, 'user')
