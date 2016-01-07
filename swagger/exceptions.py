class SwaggerServerError(Exception):
    def __init__(self, status_code, reason):
        self.status_code = status_code
        self.reason = reason

    def __str__(self):
        return '{} {}'.format(self.status_code, self.reason)


class InvalidPathError(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'got unexpected path \'{}\''.format(self.path)


class InvalidOperationError(KeyError):
    def __init__(self, operation):
        self.operation = operation

    def __str__(self):
        return 'invalid operation \'{}\''.format(self.operation)


class InvalidSecuritySchemeError(Exception):
    def __init__(self, scheme):
        self.scheme = scheme

    def __str__(self):
        return 'invalid security scheme \'{}\''.format(self.scheme)


class UnsupportedSchemeError(Exception):
    """Exception for handling unsupported schemes"""
    schemes = ('http', 'https', 'ws', 'wss',)

    def __init__(self, scheme, supported=schemes):
        self.scheme = scheme
        self.supported = supported

    def __str__(self):
        return (
            '\'{}\' is not a supported scheme. Supported schemes are: {}'
        ).format(self.scheme, ', '.join([scheme for scheme in self.supported]))
