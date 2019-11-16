from django.db.models import F
from haystack import indexes
from yoloify.pinboard.models import Pin


class PinIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    location = indexes.CharField(model_attr='goal__location__place')
    pin_count = indexes.IntegerField()

    def get_model(self):
        return Pin

    def index_queryset(self, using=None):
        return self.get_model().objects\
            .filter(user=F('goal__user'))\
            .exclude(goal__location=None)

    def prepare_pin_count(self, pin):
        return pin.goal.pin_count