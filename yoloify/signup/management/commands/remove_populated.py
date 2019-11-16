from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings

class Command(BaseCommand):

    help = 'Removes populated users and all related objects'

    def handle(self, *args, **kwargs):

        first_name_prefix = settings.TEST_POPULATION['USERS_FIRST_NAME_PREFIX']
        last_name = settings.TEST_POPULATION['USERS_LAST_NAME']

        User.objects.filter(
                first_name__startswith = first_name_prefix,
                last_name__exact = last_name
            ).delete()
