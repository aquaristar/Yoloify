import sys
import os

APP_PATH = os.path.abspath(
    os.path.join(__file__, os.path.join('../..'))
)


def load():
    sys.path.append(APP_PATH)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'yoloify.settings'
    return


def run():
    print "Starting ..."
    goals = Goal.objects.all()
    print 'Total Goals : %s' % goals.count()
    new = 0
    for goal in goals:
        try:
            pin = Pin.objects.get(user=goal.user, goal=goal)
        except Pin.DoesNotExist:
            pin = Pin(goal=goal, user=goal.user, bookmarked=True)
            pin.bookmarked_at = timezone.now()
            pin.save()
            new += 1
    print "Total created: ", new
    print "Clearing cache"
    UserSpecificCache.update(UserSpecificCache())
    print "Done ..."

if __name__ == '__main__':
    load()
    from django.utils import timezone
    from yoloify.pinboard.models import Pin, Goal
    from yoloify.pinboard.tasks import UserSpecificCache
    run()
