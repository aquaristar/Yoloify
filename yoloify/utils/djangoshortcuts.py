from hashlib import md5
from django.utils.encoding import force_bytes
from django.utils.http import urlquote

def build_template_cache_key(name, *args):
    key = ':'.join(map(lambda x: urlquote(x), map(str, args)))
    key = md5(force_bytes(key)).hexdigest()
    key = 'template.cache.%s.%s' % (name, key)
    return key
