from feedly.verbs import register
from feedly.verbs.base import Verb


class Create(Verb):
    id = 5
    infinitive = 'create'
    past_tense = 'created'

register(Create)


class Add(Verb):
    id = 6
    infinitive = 'bookmark'
    past_tense = 'bookmarked'

register(Add)


class Complete(Verb):
    id = 7
    infinitive = 'Been Here'
    past_tense = 'Been Here'

register(Complete)


class Like(Verb):
    id = 8
    infinitive = 'like'
    past_tense = 'liked'

register(Like)


class Comment(Verb):
    id = 9
    infinitive = 'Review'
    past_tense = 'Reviewed'

register(Comment)
