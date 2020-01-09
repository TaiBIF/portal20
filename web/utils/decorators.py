import functools
import json
#import logging

from django.http import HttpResponse

def json_ret(fun):

    @functools.wraps(fun)
    def wrapper(*args, **kwds):
        data = {'results': 0}
        ## offset: 0, limit: 0, endOfRecords: false
        try:
            ret = fun(*args, **kwds)
            data['results'] = ret['data']
        except Exception as e:
            data['error'] = str(e)

        return HttpResponse(json.dumps(data), content_type="application/json")

    return wrapper
