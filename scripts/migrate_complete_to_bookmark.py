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
    pins = Pin.objects.filter(complete=True)
    print "Toal: ", len(pins)
    found = 0
    for pin in pins:
        if not pin.complete:
            continue

        pin.bookmarked = True
        pin.complete = False
        pin.save()
        found += 1
    print "Found: ", found
    print "Clearing cache"
    UserSpecificCache.update(UserSpecificCache())
    print "Done"

if __name__ == '__main__':
    load()
    from yoloify.pinboard.models import Pin
    from yoloify.pinboard.tasks import UserSpecificCache
    run()
