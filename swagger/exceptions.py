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
        return 'Got unexpected path \'{}\''.format(self.path)


class InvalidOperationError(KeyError):
    def __init__(self, operation):
        self.operation = operation

    def __str__(self):
        return 'Invalid operation \'{}\''.format(self.operation)
