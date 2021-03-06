import os

from facebook_sdk.authentication import OAuth2Client, AccessToken
from facebook_sdk.client import FacebookClient
from facebook_sdk.constants import DEFAULT_GRAPH_VERSION, METHOD_POST, METHOD_GET, METHOD_DELETE
from facebook_sdk.exceptions import FacebookSDKException
from facebook_sdk.facebook_file import FacebookFile
from facebook_sdk.request import (
    FacebookBatchRequest,
    FacebookRequest,
)

APP_ID_ENV_NAME = 'FACEBOOK_APP_ID'
APP_SECRET_ENV_NAME = 'FACEBOOK_APP_SECRET'


class FacebookApp(object):
    def __init__(self, app_id, app_secret):
        """
        :type id: str
        :type secret: str
        """
        super(FacebookApp, self).__init__()
        self.id = app_id
        self.secret = app_secret

    def access_token(self):
        from facebook_sdk.authentication import AccessToken
        return AccessToken(
            access_token='{id}|{secret}'.format(
                id=self.id,
                secret=self.secret
            )
        )


class Facebook(object):
    def __init__(self, **kwargs):
        super(Facebook, self).__init__()

        self.config = {
            'app_id': os.getenv(APP_ID_ENV_NAME, kwargs.get('app_id')),
            'app_secret': os.getenv(APP_ID_ENV_NAME, kwargs.get('app_secret')),
            'default_graph_version': kwargs.get('default_graph_version', DEFAULT_GRAPH_VERSION),
            'default_access_token': kwargs.get('default_access_token'),
        }

        if not self.config['app_id']:
            raise FacebookSDKException(
                'Required "app_id" key not supplied in config and could not find '
                'fallback environment variable "{app_id_env_name}"'.format(
                    app_id_env_name=APP_ID_ENV_NAME,
                )
            )
        if not self.config['app_secret']:
            raise FacebookSDKException(
                'Required "app_secret" key not supplied in config '
                'and could not find fallback environment variable "{app_secret_env_name}"'.format(
                    app_secret_env_name=APP_SECRET_ENV_NAME,
                )
            )

        self.default_graph_version = self.config.get('default_graph_version')

        if self.config.get('default_access_token'):
            self.set_default_access_token(self.config.get('default_access_token'))

        self.app = FacebookApp(
            app_id=self.config['app_id'],
            app_secret=self.config['app_secret']
        )
        self.client = FacebookClient(request_timeout=kwargs.get('default_request_timeout'))
        self.oauth_client = OAuth2Client(
            app=self.app,
            client=self.client,
            graph_version=self.default_graph_version,
        )

    def request(self, method, endpoint, access_token=None, params=None, headers=None, graph_version=None):
        access_token = access_token or getattr(self, 'default_access_token', None)
        graph_version = graph_version or self.default_graph_version

        return FacebookRequest(
            app=self.app,
            method=method,
            access_token=access_token,
            endpoint=endpoint,
            params=params,
            headers=headers,
            graph_version=graph_version,
        )

    def send_request(self, method, endpoint, access_token=None, params=None, headers=None, graph_version=None):
        request = self.request(
            method=method,
            access_token=access_token,
            endpoint=endpoint,
            params=params,
            headers=headers,
            graph_version=graph_version,
        )
        response = self.send_facebook_request(request=request)

        return response

    def send_facebook_request(self, request):
        """
        :type request: FacebookRequest
        """
        return self.client.send_request(request=request)

    def send_batch_request(self, requests, access_token=None, graph_version=None):
        access_token = access_token or getattr(self, 'default_access_token', None)
        graph_version = graph_version or self.default_graph_version

        batch_request = FacebookBatchRequest(
            app=self.app,
            requests=requests,
            access_token=access_token,
            graph_version=graph_version,
        )

        response = self.client.send_batch_request(batch_request=batch_request)
        return response

    def set_default_access_token(self, access_token):
        if isinstance(access_token, str):
            self.default_access_token = AccessToken(access_token=access_token)
        elif isinstance(access_token, AccessToken):
            self.default_access_token = access_token
        else:
            raise ValueError('The default access token must be of type "str" or AccessToken')

    def file_to_upload(self, path):
        return FacebookFile(path=path)

    def post(self, endpoint, access_token=None, params=None, headers=None, graph_version=None):
        return self.send_request(
            method=METHOD_POST,
            access_token=access_token,
            endpoint=endpoint,
            params=params,
            headers=headers,
            graph_version=graph_version,
        )

    def get(self, endpoint, access_token=None, params=None, headers=None, graph_version=None):
        return self.send_request(
            method=METHOD_GET,
            access_token=access_token,
            endpoint=endpoint,
            params=params,
            headers=headers,
            graph_version=graph_version,
        )

    def delete(self, endpoint, access_token=None, params=None, headers=None, graph_version=None):
        return self.send_request(
            method=METHOD_DELETE,
            access_token=access_token,
            endpoint=endpoint,
            params=params,
            headers=headers,
            graph_version=graph_version,
        )
