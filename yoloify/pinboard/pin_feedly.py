from feedly.feed_managers.base import Feedly, FanoutPriority
from yoloify.signup.models import Profile
from yoloify.pinboard.pin_feed import PinFeed, UserPinFeed


class PinFeedly(Feedly):
    """
    To hook up the Feeds to your Feedly class. The Feedly class knows
    how to fanout new activities to the feeds of all your followers.
    """

    feed_classes = dict(
        normal=PinFeed,
    )

    user_feed_class = UserPinFeed

    def add_pin(self, pin, actor_id, verb):
        activity = pin.create_activity(actor_id, verb)
        # add user activity adds it to the user feed, and starts the fanout
        self.add_user_activity(actor_id, activity)

    def remove_pin(self, actor_id, activity):
        ## removes the pin from the user's followers feeds
        self.remove_user_activity(actor_id, activity)

    def get_user_follower_ids(self, user_id):
        profile = Profile.objects.get(user_id=user_id)
        ids = profile.followers.all().values_list('user_id', flat=True)
        return {FanoutPriority.HIGH: ids}

feedly = PinFeedly()
