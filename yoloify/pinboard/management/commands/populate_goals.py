import random
import string
import StringIO
from PIL import Image
from django.core.files import File

from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.models import User
from django.conf import settings

from yoloify.pinboard.models import Goal, Location


class Command(BaseCommand):

    help = 'Populates the database with fake goals for testing purposes'

    @staticmethod
    def gen_image(flavor, width, height, filename = None):

        pixel_width = 5
        pixel_height = 5

        max_red = 127
        max_green = 127
        max_blue = 127

        if flavor in ['RED', 'RANDOM']:
            max_red = 255
        if flavor in ['GREEN', 'RANDOM']:
            max_green = 255
        if flavor in ['BLUE', 'RANDOM']:
            max_blue = 255

        data = []
        for i in xrange(height):
            if i % pixel_height == 0:
                line = []
                for j in xrange(width):
                    if j % pixel_width == 0:
                        pixel = (random.randint(0, max_red),
                                 random.randint(0, max_green),
                                 random.randint(0, max_blue))
                    line.append(pixel)
            data += line

        image = Image.new('RGBA', (width, height))
        image.putdata(data)

        if filename:
            image.save(filename)

        buf = StringIO.StringIO()
        image.save(buf, format='JPEG')
        buf.seek(0)
        return InMemoryUploadedFile(buf, None, '%s.jpg' % Command.gen_word(), 'image/jpeg', buf.len, None)

    @staticmethod
    def gen_word(max_length = 10):
        return "".join(random.sample(string.lowercase, random.randint(1, max_length)))

    @staticmethod
    def gen_sentence(max_word_count = 15):
        return " ".join([Command.gen_word() for _ in xrange(max_word_count)])

    @staticmethod
    def gen_title(max_word_count = 15):
        return string.capwords(Command.gen_sentence(max_word_count))

    def handle(self, *args, **kwargs):
        
        users_last_name = settings.TEST_POPULATION['USERS_LAST_NAME']
        goals_count = settings.TEST_POPULATION['GOALS_COUNT']
        goal_img_max_width = settings.TEST_POPULATION['GOAL_IMG_MAX_WIDTH']
        goal_img_max_height = settings.TEST_POPULATION['GOAL_IMG_MAX_HEIGHT']

        users = list(User.objects.filter(last_name = users_last_name))

        for i in xrange(goals_count):
            image = Command.gen_image(
                random.choice(['RED', 'GREEN', 'BLUE', 'RANDOM']),
                random.randint(goal_img_max_width / 2, goal_img_max_width),
                random.randint(goal_img_max_height / 2, goal_img_max_height),
            )
            goal = Goal(
                user=random.choice(users),
                title=Command.gen_title(),
                location=Location.objects.create(point='POINT(%s %s)' % (random.random()*360 - 180, random.random()*180 - 90))
            )
            goal.image = image
            goal.save()
