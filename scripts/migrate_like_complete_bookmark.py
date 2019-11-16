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
    print "Delete duplications"
    duplications = Pin.objects.values('goal', 'user').annotate(Count('id'))
    for d in duplications:
        if d['id__count'] <= 1:
            continue
        print d
        pins = Pin.objects.filter(user=d['user'], goal=d['goal']).order_by('-id')
        for pin in pins[1:]:
            pin.delete()

    print "migrate likes",
    likes = Like.objects.filter(end_valid__isnull=True)
    print len(likes)
    total = 0
    for like in likes:
        pin, created = Pin.objects.get_or_create(user=like.user, goal=like.goal)
        pin.liked = True
        pin.save()
        if created:
            total += 1
    print "Total created: ", total

    print "migrate bookmarked",
    pins = Pin.objects.filter(end_valid__isnull=True)
    print len(pins)
    total = 0
    for pin in pins:
        new_pin, created = Pin.objects.get_or_create(user=pin.user, goal=pin.goal)
        new_pin.bookmarked = True
        new_pin.save()
        if created:
            total += 1
    print "Toal created: ", total

    print "migrate completed",
    pins = Pin.objects.filter(completed__isnull=True)
    print len(pins)
    for pin in pins:
        new_pin, created = Pin.objects.get_or_create(user=pin.user, goal=pin.goal)
        new_pin.complete = True
        new_pin.save()
        if created:
            total += 1
    print "Toal created: ", total

    print "Migration Done"

    print "Clearing Cache"
    update_pin_like_bookmark_count()
    periodic_cache_updates()
    UserSpecificCache.update(UserSpecificCache())
    print "Done"


if __name__ == '__main__':
    load()
    from django.db.models import Count
    from yoloify.pinboard.models import Pin, Like
    from yoloify.pinboard.tasks import update_pin_like_bookmark_count, periodic_cache_updates, UserSpecificCache
    print "Don't run it's invalid now"
    #run()
