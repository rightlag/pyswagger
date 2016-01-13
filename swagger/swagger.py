import json
import os
import requests

from requests.auth import _basic_auth_str
from exceptions import (
    SwaggerServerError,
    InvalidPathError,
    InvalidOperationError,
    UnsupportedSchemeError
)


class Swagger(object):
    ResponseError = SwaggerServerError
    DefaultSchemes = ('http', 'https', 'ws', 'wss',)
    DefaultFormat = 'application/json'
    DefaultOperations = ('get', 'put', 'post', 'delete', 'options', 'head',
                         'patch',)

    def __init__(self):
        self._baseUri = None
        self._session = requests.Session()

    @property
    def baseUri(self):
        return self._baseUri

    @baseUri.setter
    def baseUri(self, value):
        self._baseUri = value

    def _set_headers(self, obj):
        """Set the `Accept` and `Content-Type` headers for the request.

        :type obj: dict
        :param kwargs: Either the schema definition object or the
          operation object
        """
        if 'consumes' in obj:
            try:
                # Try to index the MIME type assigned in the request.
                # If the MIME type does not exist, assign the index to 0
                # and assign the `Content-Type` header to use the first
                # index in the `consumes` list object.
                index = obj.pop('index')
            except KeyError:
                index = 0
            finally:
                self._session.headers['Content-Type'] = obj['consumes'][index]
        if 'produces' in obj:
            self._session.headers['Accept'] = '*/*'

    def _set_security_definitions(self, schema):
        """Set the global security definitions for the schema.

        :type schema: dict
        :param schema: schema dictionary object
        """
        if 'securityDefinitions' in schema:
            for auth, definition in schema['securityDefinitions'].iteritems():
                if definition['type'] == 'apiKey':
                    parameterIn = definition['in']
                    if parameterIn == 'header':
                        # Assign the `apiKey` header used for token
                        # authentication.
                        self._session.headers[definition['name']] = None
                    elif parameterIn == 'query':
                        # If the `parameterIn` object is passed as a
                        # query parameter, then do not assign it, for it
                        # will be handled in the operation callback.
                        pass
                if definition['type'] == 'basic':
                    # Assign the `Authorization` header used for Basic
                    # authentication.
                    self._session.headers['Authorization'] = None

    def _get_scheme(self, scheme=None):
        """Return the scheme to be used for issuing a request.

        :type scheme: str
        :param scheme: The scheme name (http, https, ws, wss)
        """
        if scheme:
            try:
                index = self.schemes.index(scheme)
            except ValueError:
                # If the scheme does not exist, raise an
                # `UnsupportedSchemeError` exception.
                raise UnsupportedSchemeError(scheme, supported=self.schemes)
            return self.schemes[index]
        else:
            if len(self.schemes) < 2:
                # If the length of the `schemes` object is less than 2,
                # then index the first scheme from the `schemes` object
                # and return it.
                return self.schemes[0]

    @staticmethod
    def load(path):
        """Load Swagger schema file and return a new client instance.

        :type path: str
        :param path: The absolute or relative path to the schema file
        """
        path = os.path.join(os.path.dirname(__file__), path)
        if not os.path.exists(path):
            raise IOError('{} does not exist'.format(path))
        with open(path, 'rb') as fp:
            schema = json.loads(fp.read())
            instance = Swagger()
            # Assign the Swagger version to the client instance.
            instance.Version = schema.pop('swagger')
            for field, obj in schema.iteritems():
                setattr(instance, field, obj)
            if not hasattr(instance, 'schemes'):
                instance.schemes = instance.DefaultSchemes
            # If the scheme is not explicitly defined when issuing the
            # request, the `DefaultScheme` is assigned.
            instance.DefaultScheme = instance.schemes[0]
            # Assign the `_baseUri` property of the client. The request
            # protocol is assigned when issuing the request.
            instance._baseUri = '{host}{basePath}'.format(
                host=instance.host,
                basePath=(
                    instance.basePath if hasattr(instance, 'basePath') else ''
                )
            )
            instance._set_security_definitions(schema)
            # Assign the global headers of the schema. Headers can be
            # overridden in the operation callback method.
            instance._set_headers(schema)
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
            try:
                # If the `scheme` keyword argument is present, override
                # the default scheme. Otherwise, use the default scheme
                # for issuing the request.
                scheme = kwargs['scheme']
            except KeyError:
                scheme = self.DefaultScheme
            scheme = self._get_scheme(scheme=scheme)
            fmt = kwargs.pop('format', self.DefaultFormat)
            if 'consumes' in operation:
                index = operation['consumes'].index(fmt)
                operation['index'] = index
            if 'security' in operation:
                try:
                    auth = kwargs['auth']
                    securityDefinitions = self.securityDefinitions
                    for security in operation['security']:
                        for name in security.iterkeys():
                            if securityDefinitions[name]['type'] == 'apiKey':
                                # If the security object name key exists
                                # in the request header, then assign the
                                # value of the request header the `auth`
                                # token, otherwise, pass it as a query
                                # parameter.
                                if name in self._session.headers:
                                    self._session.headers[name] = auth
                                else:
                                    kwargs[name] = auth
                            if securityDefinitions[name]['type'] == 'basic':
                                auth = _basic_auth_str(*auth)
                                self._session.headers['Authorization'] = auth
                    kwargs.pop('auth')
                except KeyError:
                    pass
            body = kwargs.pop('body', {})
            # Override the default headers defined in the root schema.
            self._set_headers(operation)
            # Use string interpolation to replace placeholders with
            # keyword arguments.
            path = path.format(**kwargs)
            url = (
                '{scheme}://{baseUri}{path}'
            ).format(scheme=scheme, baseUri=self._baseUri, path=path)
            # If the `body` keyword argument exists, remove it from the
            # keyword argument dictionary and pass it as an argument
            # when issuing the request.
            try:
                res = self._session.request(fn, url, params=kwargs, data=body)
            except requests.exceptions.SSLError:
                # If the request fails via a `SSLError`, re-instantiate
                # the request with the `verify` argument assigned  to
                # `False`.
                res = self._session.request(fn, url, params=kwargs, data=body,
                                            verify=False)
            if res.status_code not in range(200, 300):
                # If the response status code is a non-2XX code, raise a
                # `ResponseError`. The `reason` variable attempts to
                # retrieve the `description` key if it is provided in
                # the `response` object. Otherwise, the default response
                # `reason` is used.
                try:
                    response = operation['responses'][str(res.status_code)]
                    reason = response.get('description', res.reason)
                    status_code, reason = res.status_code, reason
                except KeyError:
                    # Use the default `status_code` and `reason`
                    # returned from the response.
                    status_code, reason = res.status_code, res.reason
                raise self.ResponseError(status_code, reason)
            return res
        if fn not in self.DefaultOperations:
            # If the method does not exist in the `DefaultOperations`,
            # raise an `InvalidOperationError` exception.
            raise InvalidOperationError(fn)
        return callback.__get__(self)

    def __str__(self):
        return '{}:{}'.format(self.__class__.__name__, self.host)

    def __repr__(self):
        return str(self)
