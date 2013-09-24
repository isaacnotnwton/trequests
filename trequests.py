from os import path
from tornalet import asyncify
from tornado.httpclient import AsyncHTTPClient
from requests import adapters, session as requests_session

__version__ = get_version_string()


# Don't know how to handle this yet, so just mock it out for now
adapters.extract_cookies_to_jar = lambda a, b, c: None


class AsyncHTTPAdapter(adapters.HTTPAdapter):
    """A python-requests HTTP/HTTPS adapter that uses the Tornado
    AsyncHTTPClient and greenlets (via the tornalet library) to perform a
    non-blocking call inside the Tornado IOLoop whenever a
    requests.[get/post/put/delete/request]() call is made. It then wraps the
    tornado.httpclient.HTTPResponse as a requests.models.Response instance and
    returns so that any library calling requests gets what it expects
    (mostly).
    """

    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):

        http_client = AsyncHTTPClient()
        # This where the magic happens, tornalet.asyncify wraps the parent
        # call in a greenlet that can be swapped out the same as any
        # aync tornado IO handler call.
        resp = asyncify(http_client.fetch)(request=request.url,
                                           method=request.method,
                                           body=request.body,
                                           headers=request.headers)

        # We probably don't get this from any of the tornado adaptors, so
        # we stub it out as Unknown
        resp.reason = 'Unknown'
        resp.content = resp.body
        r = self.build_response(request, resp)
        # Reset the code and content as they're not parsed by build_response
        r.status_code = resp.code
        r._content = resp.content
        return r


def setup_session(session=None, mounts=None):
    if session is None:
        session = requests_session
    if mounts is None:
        mounts = ('http://', 'https://')

    for mount in mounts:
        session.mount(mount, AsyncHTTPAdapter())


def get_version_string():
    return open(path.join(path.dirname(__file__),
                'version.txt'), 'r').read().strip()


def get_version():
    return get_version_string().split('.')
