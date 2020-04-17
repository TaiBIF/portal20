from django.core.cache import cache

def get_cache_or_set(key, value_or_func, timeout=2592000):
    '''default_timeout: 60*60*24*30'''
    if value:= cache.get(key):
        return value
    else:
        v = None
        if callable(value_or_func):
            v = value_or_func()
        else:
            v = value_or_func
        cache.set(key, v, timeout)
        return v
