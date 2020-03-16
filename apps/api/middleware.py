from django.http import HttpResponse
import json
def DebugToolbarForJsonMiddleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        response = get_response(request)
        if request.GET.get('debug', '') and \
           response.get('Content-Type', '') == 'application/json':
            #data = json.dumps(response.content.decode())
            return HttpResponse('''<html><body>
            <script>
var data = %s;
            document.write("<pre>");
            document.write(JSON.stringify(data, null, 4));
            document.write("</pre>");
            </script>
            </body></html>'''%response.content.decode())
        return response

    return middleware
