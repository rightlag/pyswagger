import requests


from urllib.parse import urlparse
from .exceptions import SwaggerServerError
from .exceptions import InvalidPathError
from .exceptions import InvalidOperationError


class Swagger(object):
    ResponseError = SwaggerServerError
    DefaultFormat = 'application/json'
    DefaultOperations = ('get', 'put', 'post', 'delete', 'options', 'head',
                         'patch',)

    def __init__(self):
        self._baseUri = None
        self._timeout = 10.0
        self._session = requests.Session()

    @property
    def baseUri(self):
        return self._baseUri

    @baseUri.setter
    def baseUri(self, baseUri):
        if hasattr(self, 'basePath'):
            baseUri += self.basePath
        self._baseUri = baseUri

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, timeout):
        self._timeout = float(timeout)

    @property
    def auth(self):
        return self._session.auth

    @auth.setter
    def auth(self, auth):
        for _, definition in list(self.securityDefinitions.items()):
            if definition['type'] == 'apiKey':
                parameterIn = definition['in']
                if parameterIn == 'header':
                    # Assign the `apiKey` header used for token
                    # authentication.
                    self._session.headers[definition['name']] = auth
            elif definition['type'] == 'basic':
                # Assign the `Authorization` header used for Basic
                # authentication.
                self._session.auth = auth

    @property
    def headers(self):
        return self._session.headers

    @headers.setter
    def headers(self, obj):
        """Set the `Accept` and `Content-Type` headers for the request.

        :type obj: dict
        :param obj: Either the schema definition object or the
          operation object
        """
        if 'consumes' in obj:
            # Try to index the MIME type assigned in the request. If the
            # MIME type does not exist, assign the index to 0 and assign
            # the `Content-Type` header to use the first index in the
            # `consumes` list object.
            index = obj.pop('index', 0)
            self._session.headers['Content-Type'] = obj['consumes'][index]
        if 'produces' in obj:
            self._session.headers['Accept'] = '*/*'

    @staticmethod
    def load(url):
        """Load Swagger schema file and return a new client instance.

        :type url: str
        :param url: The URL to the Swagger schema
        """
        response = requests.get(url)
        if response.status_code not in list(range(200, 300)):
            response.raise_for_status()
        schema = response.json()
        instance = Swagger()
        # Assign the Swagger version to the client instance.
        instance.Version = schema.pop('swagger')
        for field, obj in list(schema.items()):
            setattr(instance, field, obj)
        # Assign the `_baseUri` property of the client. The request
        # protocol is assigned when issuing the request.
        url = urlparse(url)
        instance._baseUri = '{scheme}://{host}{basePath}'.format(
            scheme=url.scheme,
            host=instance.host,
            basePath=(
                instance.basePath if hasattr(instance, 'basePath') else ''
            )
        )
        # Assign the global headers of the schema. Headers can be
        # overridden in the operation callback method.
        instance.headers = schema
        return instance

    def __getattr__(self, fn):
        def callback(self, *args, **kwargs):
            """Callback method for issuing requests via the operations
            defined in the paths"""
            try:
                # If the `path` argument is not passed, raise a
                # `ValueError` exception.
                path = args[0]
            except IndexError:
                raise ValueError('Path argument not provided')
            if path not in self.paths:
                # If the `path` does not exist, raise `InvalidPathError`
                # exception.
                raise InvalidPathError(path)
            operation = self.paths[path][fn]
            if 'consumes' in operation:
                fmt = kwargs.pop('format', self.DefaultFormat)
                try:
                    index = operation['consumes'].index(fmt)
                except ValueError:
                    index = 0
                finally:
                    operation['index'] = index
            if 'security' in operation:
                if 'auth' in kwargs:
                    auth = kwargs.pop('auth')
                    self.auth = auth
            # If the `body` keyword argument exists, remove it from the
            # keyword argument dictionary and pass it as an argument
            # when issuing the request.
            body = kwargs.pop('body', {})
            # Override the default headers defined in the root schema.
            self.headers = operation
            # Use string interpolation to replace placeholders with
            # keyword arguments.
            path = path.format(**kwargs)
            url = '{baseUri}{path}'.format(baseUri=self._baseUri, path=path)
            try:
                response = self._session.request(
                    fn, url, params=kwargs, data=body, timeout=self._timeout
                )
            except requests.exceptions.SSLError:
                # If the request fails via a `SSLError`, re-instantiate
                # the request with the `verify` argument assigned  to
                # `False`.
                response = self._session.request(
                    fn, url, params=kwargs, data=body, verify=False,
                    timeout=self._timeout
                )
            if response.status_code not in list(range(200, 300)):
                # If the response status code is a non-2XX code, raise a
                # `ResponseError`. The `reason` variable attempts to
                # retrieve the `description` key if it is provided in
                # the `response` object. Otherwise, the default response
                # `reason` is used.
                try:
                    reason = (
                        operation['responses'][str(response.status_code)].get(
                            'description', response.reason
                        )
                    )
                except KeyError:
                    # Use the default `status_code` and `reason`
                    # returned from the response.
                    reason = response.reason
                raise self.ResponseError(response.status_code, reason)
            return response
        if fn not in self.DefaultOperations:
            # If the method does not exist in the `DefaultOperations`,
            # raise an `InvalidOperationError` exception.
            raise InvalidOperationError(fn)
        return callback.__get__(self)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self._baseUri)
