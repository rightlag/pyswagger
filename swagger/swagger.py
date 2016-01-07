import json
import os
import requests

from exceptions import (
    SwaggerServerError,
    InvalidPathError,
    InvalidOperationError,
    UnsupportedSchemeError
)


class Swagger(object):
    ResponseError = SwaggerServerError
    DefaultScheme = 'http'
    DefaultSchemes = ('http', 'https', 'ws', 'wss',)
    DefaultFormat = 'application/json'

    def __init__(self):
        self._baseUri = None
        self._security = {}
        self._session = requests.Session()

    @property
    def baseUri(self):
        return self._baseUri

    @baseUri.setter
    def baseUri(self, value):
        self._baseUri = value

    def _setheaders(self, **kwargs):
        """Set the `Accept` and `Content-Type` headers for the request"""
        if 'consumes' in kwargs:
            # index of the MIME type returned from the request
            index = kwargs.get('index', 0)
            self._session.headers['Content-Type'] = kwargs['consumes'][index]
            # remove the `index` key
            kwargs.pop('index')
        if 'produces' in kwargs:
            self._session.headers['Accept'] = '*/*'
        if 'securityDefinitions' in kwargs:
            for auth, definition in kwargs['securityDefinitions'].iteritems():
                if definition['type'] == 'apiKey':
                    self._security.update(definition)
                    parameterIn = definition['in']
                    if parameterIn == 'header':
                        # assign the `apiKey` header
                        self._session.headers[definition['name']] = None
                    break

    def _setschemes(self, schema):
        """Set the default schemes if the `schemes` key does not exist
        in the `schema` object

        :type schema: dict
        :param schema: The Swagger schema specification object
        """
        if 'schemes' not in schema:
            setattr(self, 'schemes', self.DefaultSchemes)

    def _getscheme(self, scheme=None):
        if scheme:
            try:
                index = self.schemes.index(scheme)
                return self.schemes[index]
            except ValueError:
                raise UnsupportedSchemeError(scheme, supported=self.schemes)
        else:
            if len(self.schemes) < 2:
                return self.schemes[0]

    @classmethod
    def load(cls, path):
        """Load Swagger schema file and return a new client instance

        :type path: str
        :param path: The absolute or relative path to the schema file
        """
        path = os.path.join(os.path.dirname(__file__), path)
        if not os.path.exists(path):
            raise IOError('{} does not exist'.format(path))
        with open(path, 'rb') as fp:
            schema = json.loads(fp.read())
            instance = cls()
            # assign the Swagger version to the instance object
            instance.Version = schema.pop('swagger')
            for field, obj in schema.iteritems():
                setattr(instance, field, obj)
            # set the `_baseUri` property of the client -- the protocol
            # is assigned when making the request
            instance._baseUri = '{host}{basePath}'.format(
                host=instance.host,
                basePath=instance.basePath if instance.basePath else '/'
            )
            instance._setschemes(schema)
            # set the global headers of the schema -- headers can be overridden
            # in the operation callback
            instance._setheaders(**schema)
            return instance

    def __getattr__(self, fn):
        def callback(self, *args, **kwargs):
            """Callback method for issuing requests via the operations
            defined in the paths"""
            # HTTP request path -- first argument of method being called
            path = args[0]
            if path not in self.paths:
                # path does not exist -- raise `InvalidPathError`
                raise InvalidPathError(path)
            try:
                # get dictionary object containing available methods
                operation = self.paths[path][fn]
            except KeyError:
                # method does not exist -- raise `InvalidOperationError`
                raise InvalidOperationError(fn)
            # assign the scheme via keyword argument -- default is HTTP
            try:
                scheme = kwargs['scheme']
                scheme = self._getscheme(scheme=scheme)
            except KeyError:
                # if the `scheme` keyword argument is not passed use the
                # default scheme `http`
                scheme = self._getscheme(scheme=self.DefaultScheme)
            # use string interpolation to replace placeholders with keyword
            # arguments
            path = path.format(**kwargs)
            url = (
                '{scheme}://{baseUri}{path}'
            ).format(scheme=scheme, baseUri=self._baseUri, path=path)
            # request body -- remove from keyword arguments to prevent being
            # passed as query parameters
            body = kwargs.pop('body', {})
            fmt = kwargs.pop('format', self.DefaultFormat)
            if 'consumes' in operation:
                index = operation['consumes'].index(fmt)
                operation['index'] = index
            if 'auth' in kwargs and self._security:
                auth = kwargs['auth']
                # assign the authentication token value to either the request
                # header or query parameter
                if self._security['in'] == 'header':
                    self._session.headers[self._security['name']] = auth
                    # remove the `auth` key to prevent it from being passed as
                    # a query parameter
                    kwargs.pop('auth')
                elif self._security['in'] == 'query':
                    kwargs[self._security['name']] = auth
            # override global headers if operation contains custom headers
            self._setheaders(**operation)
            try:
                res = self._session.request(fn, url, params=kwargs, data=body)
            except requests.exceptions.SSLError:
                res = self._session.request(fn, url, params=kwargs, data=body,
                                            verify=False)
            if res.status_code not in range(200, 300):
                # non 2xx status code
                try:
                    response = operation['responses'][str(res.status_code)]
                    reason = response.get('description', res.reason)
                    status_code, reason = res.status_code, reason
                except KeyError:
                    # status code does not exist in list of responses
                    status_code, reason = res.status_code, res.reason
                raise self.ResponseError(status_code, reason)
            return res
        return callback.__get__(self)

    def __str__(self):
        return '{}:{}'.format(self.__class__.__name__, self.host)

    def __repr__(self):
        return str(self)
