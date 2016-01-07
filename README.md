# pyswagger

pyswagger 0.1.0
Released: 7-Jan-2016

# Release Notes

  - **Current**
    - Reads Swagger schema specifications
    - Creates a `client` object used to instantiate requests to paths defined in the schema
    - Supports `apiKey` authentication
    - Supports common request methods (e.g. `GET`, `POST`, `PUT`, and `DELETE`)

  - **Roadmap**
     - Support for OAuth (maybe) and basic authentication
     - Support for Swagger schema specifications to be read from hosted sites instead of reading them from local device

# Introduction

pyswagger is a Python toolkit that reads any JSON formatted [http://swagger.io/](Swagger) (Open API) schema and generates methods for the [http://swagger.io/specification/#operationObject](operations) defined in the schema.

# Getting started

To use the pyswagger client, import the `Swagger` class from the `swagger` module. The following example uses the [http://petstore.swagger.io/](Swagger Petstore) API.

```python
from swagger import Swagger

client = Swagger.load('../schemas/petstore.json')
res = client.get('/pet/findByStatus', status='sold')
print res.json()
```

This returns a list of `Pet` objects whose `status` attribute is assigned `sold`.

The `status` keyword argument is located within the list of parameters of the `/pet/findByStatus` path in the `petstore.json` schema.

# Query parameters

Endpoints that accept optional or required query parameters can be passed as keyword arguments to the method call.

# Endpoints containing IDs

For endpoints that contain IDs (e.g. `/pet/2`), pyswagger uses string interpolation to match the ID with the respective keyword argument. The following example simulates a `GET` request that will return a pet with ID `2`:

```python
from swagger import Swagger

client = Swagger.load('../schemas/petstore.json')
res = client.get('/pet/{petId}', petId=2)
print res.json()
```

The `{petId}` placeholder is matched in the endpoint string and is replaced with the value of the `petId` keyword argument.

# Requests containing a payload

For requests that require a request payload, the `body` keyword argument can be passed as an argument to the method. The value of the `body` argument *should* be [https://en.wikipedia.org/wiki/Serialization](serialized). The following example simulates a `POST` request that will create a new pet:

```python
from swagger import Swagger

data = {
    'id': 0,
    'category': {
        'id': 0,
        'name': 'string',
    },
    'name': 'doggie',
    'photoUrls': [
        'string',
    ],
    'tags': [
        {
            'id': 0,
            'name': 'string',
        }
    ],
    'status': 'available',
}
# serialize the data in JSON format
data = json.dumps(data)
client = Swagger.load('../schemas/petstore.json')
res = client.post('/pet', body=data, auth='special-key')
print res.status_code
```

**Note:** Some endpoints do not return a response body. Therefore, invoking the `.json()` method on the response object will raise an exception.

The example above  also includes the `auth` keyword argument which is explained in further detail in the next section.

# Authenticated endpoints

Authentication is sometimes required to access some or all endpoints of a web API. Since pyswagger is a client-side toolkit, it does not support authentication schemes such as [https://en.wikipedia.org/wiki/OAuth](OAuth). However, if the endpoint requires an access token to make a request, then the `auth` keyword argument can be supplied.

## Using the `auth` keyword argument

Swagger uses [http://swagger.io/specification/#securityDefinitionsObject](Security Definitions) to define security schemes available to be used in the specification. The `in` field states the location of the API key which is either the `query` or the `header`.

If a security definition exists in the schema, pyswagger inspects the value of the `in` field and automatically assigns it as a request header or a query parameter. Therefore, when using the `auth` keyword, it is not required to specify the location of the API key.
