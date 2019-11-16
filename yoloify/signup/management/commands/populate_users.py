import random
import string

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings

from yoloify.signup.models import Profile

class Command(BaseCommand):

    help = 'Populates the database with fake users for testing purposes'

    def handle(self, *args, **kwargs):

        users_num = settings.TEST_POPULATION['USERS_COUNT']
        user_slubs = set()
        while len(user_slubs) != users_num:
            user_slubs.add("".join(random.sample(string.uppercase, 3)))
        user_slubs = list(user_slubs)
        
        def get_first_name(user_no):
            return "%s_%s" % (settings.TEST_POPULATION['USERS_FIRST_NAME_PREFIX'], user_slubs[user_no])

        def get_last_name(user_no):
            return settings.TEST_POPULATION['USERS_LAST_NAME']

        for i in xrange(users_num):

            user = User(
                username = '%s %s' % (get_first_name(i), get_last_name(i)),   # temporary placeholder
                first_name = get_first_name(i),
                last_name = get_last_name(i),
                email = '%s@example.com' % get_first_name(i),
            )
            user.set_password('qwerty') # WARNING: for testing purposes only!
            user.save()
            user.username = str(user.id)
            user.save()

            profile = Profile(user = user)
            profile.save()

        max_followers_count = min(users_num / 2, 100)
        for i in xrange(users_num):

            profile = Profile.objects.get(
                user__first_name = get_first_name(i),
                user__last_name = get_last_name(i),
            )
            followers_no = random.sample(xrange(users_num), max_followers_count)
            if i in followers_no:
                followers_no.remove(i)

            for follower_no in followers_no:
                follower_profile = Profile.objects.get(
                    user__first_name = get_first_name(follower_no),
                    user__last_name = get_last_name(follower_no),
                )
                profile.followers.add(follower_profile)
