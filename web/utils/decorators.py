import functools
import json
#import logging

from django.http import HttpResponse

def json_ret(fun):

    @functools.wraps(fun)
    def wrapper(*args, **kwds):
        ret = {'data': {}}
        ## offset: 0, limit: 0, endOfRecords: false
        try:
            fun_ret = fun(*args, **kwds)
            ret['data'] = fun_ret['data']
        except Exception as e:
            ret['error'] = str(e)

        return HttpResponse(json.dumps(ret), content_type="application/json")

    return wrapper
