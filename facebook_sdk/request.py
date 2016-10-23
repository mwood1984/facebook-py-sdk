from facebook_sdk.constants import DEFAULT_GRAPH_VERSION, METHOD_POST
from facebook_sdk.exceptions import FacebookSDKException
from facebook_sdk.utils import force_slash_prefix

MAX_REQUEST_BY_BATCH = 50

try:
    import simplejson as json
except ImportError:
    import json

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


class FacebookRequest(object):
    """ A Facebook Request.

    """

    def __init__(self, app=None, access_token=None, method=None, endpoint=None, params=None, headers=None,
                 graph_version=None):
        super(FacebookRequest, self).__init__()

        # Default empty dicts for dict params.
        headers = {} if headers is None else headers
        params = {} if params is None else params
        graph_version = DEFAULT_GRAPH_VERSION if graph_version is None else graph_version

        self.app = app
        self.access_token = access_token
        self.method = method
        self.endpoint = endpoint
        self.graph_version = graph_version
        self.headers = headers
        self._params = params

    @property
    def params(self):
        """ The url params.

        :rtype: dict
        """
        params = self._params.copy() if self.method != METHOD_POST else {}
        if self.access_token:
            params.update(dict(access_token=str(self.access_token)))

        return params

    @property
    def post_params(self):
        """ The post params.

        :rtype: object
        """
        if self.method == METHOD_POST:
            return self._params.copy()

        return None

    @property
    def url(self):
        """ The relative url to the graph api.

        :rtype: str
        """
        return force_slash_prefix(self.graph_version) + force_slash_prefix(self.endpoint)

    @property
    def url_encode_body(self):
        """ Convert the post params to a urlencoded str

        :rtype: str
        """
        params = self.post_params

        return urlencode(params) if params else None

    def add_headers(self, headers):
        """ Append headers to the request.

        :param headers: a list of headers
        """
        for header in headers:
            self.headers.update(header)


class FacebookBatchRequest(FacebookRequest):
    """ A Facebook Batch Request.

    """

    def __init__(self, app=None, requests=None, access_token=None, graph_version=None):
        """
        :param requests: a list of FacebookRequest
        :param access_token: the access token for the batch request
        :param graph_version: the graph version for the batch request
        """
        graph_version = graph_version or DEFAULT_GRAPH_VERSION

        super(FacebookBatchRequest, self).__init__(
            app=app,
            access_token=access_token,
            graph_version=graph_version,
            method=METHOD_POST,
            endpoint='',
        )

        self.requests = []

        if requests:
            self.add(request=requests)

    def add(self, request, name=None):
        """ Append a request or a set of request to the baths.

        :param request: an instance, list or dict of FacebookRequest
        :param name: the name of the request. keep it as None if you provide a set of requests
        """

        if isinstance(request, list):
            for index, req in enumerate(request):
                self.add(req, index)
            return

        if isinstance(request, dict):
            for key, req in request.items():
                self.add(req, key)
            return

        if not isinstance(request, FacebookRequest):
            raise FacebookSDKException('Arguments must be of type dict, list or FacebookRequest.')

        self._add_access_token(request)

        self.requests.append({
            'name': str(name),
            'request': request,
        })

    def _add_access_token(self, request):
        """ Set the batch request access token to the request if wasn't provided.

        :type request: FacebookRequest
        """

        if not request.access_token:
            access_token = self.access_token

            if not access_token:
                raise FacebookSDKException('Missing access token on FacebookRequest and FacebookBatchRequest')

            request.access_token = self.access_token

    def prepare_batch_request(self):
        params = {
            'batch': self.requests_to_json(),
            'include_headers': True,
        }
        self._params.update(params)

    def request_entity_to_batch_array(self, request, request_name):
        """ Convert a FacebookRequest entity to a request batch representation.

        :param request: a FacebookRequest
        :param request_name: the request name
        :return: a dict with the representation of the request
        """

        batch = {
            'headers': request.headers,
            'method': request.method,
            'relative_url': request.url,
        }

        encoded_body = request.url_encode_body
        if encoded_body:
            batch['body'] = encoded_body

        if request_name is not None:
            batch['name'] = request_name

        if request.access_token != self.access_token:
            batch['access_token'] = str(request.access_token)

        return batch

    def requests_to_json(self):
        """ Convert the requests to json."""
        json_requests = [
            self.request_entity_to_batch_array(
                request=request['request'],
                request_name=request['name']
            ) for request in self.requests
        ]

        return json.dumps(json_requests)

    def validate_batch_request_count(self):

        """ Validate the request count before sending them as a batch.

            :raise FacebookSDKException
        """
        requests_count = len(self.requests)

        if not requests_count:
            raise FacebookSDKException('Empty batch requests')
        if requests_count > MAX_REQUEST_BY_BATCH:
            raise FacebookSDKException('The limit of requests in batch is %d' % MAX_REQUEST_BY_BATCH)

    def __iter__(self):
        return iter(self.requests)
