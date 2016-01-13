import httplib
import json
import unittest

from swagger import Swagger


class SwaggerTestCast(unittest.TestCase):
    def setUp(self):
        # Load the schema to create the client object.
        self.client = Swagger.load('../schemas/petstore.json')
        self.data = {
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

    @property
    def pet(self):
        data = json.dumps(self.data)
        res = self.client.post('/pet', body=data, auth='special-key')
        return res.json()

    def test_swagger_version(self):
        """Assert Swagger version is '2.0'"""
        self.assertEqual(self.client.Version, '2.0')

    def test_set_headers(self):
        pass

    def test_swagger_default_scheme(self):
        # Only scheme for `petstore.json` is `http`.
        self.assertEqual(self.client.DefaultScheme, 'http')

    def test_create_pet_endpoint(self):
        data = json.dumps(self.data)
        expected_url = 'http://petstore.swagger.io/v2/pet'
        res = self.client.post('/pet', body=data, auth='special-key')
        self.assertEqual(res.url, expected_url)
        self.assertTrue(isinstance(res.json(), dict))
        self.assertEqual(res.status_code, httplib.OK)

    def test_get_pet_by_id_endpoint(self):
        petId = self.pet['id']
        res = self.client.get('/pet/{petId}', petId=petId)
        self.assertEqual(res.status_code, httplib.OK)

    def test_find_pets_by_status_endpoint(self):
        statuses = ('available', 'pending', 'sold',)
        for status in statuses:
            res = self.client.get('/pet/findByStatus', status=status)
            expected_url = (
                'http://petstore.swagger.io/v2/pet/findByStatus?status={}'
            ).format(status)
            self.assertEqual(res.url, expected_url)
            self.assertEqual(res.status_code, httplib.OK)
            self.assertTrue(isinstance(res.json(), list))

    def test_find_pets_by_tags_endpoint(self):
        tags = ('tag1', 'tag2', 'tag3',)
        tags = ', '.join([tag for tag in tags])
        res = self.client.get('/pet/findByTags', tags=tags)
        self.assertEqual(res.status_code, httplib.OK)
        self.assertTrue(isinstance(res.json(), list))

    def test_find_pet_by_id_endpoint(self):
        petId = self.pet['id']
        res = self.client.get('/pet/{petId}', petId=petId)
        self.assertEqual(res.status_code, httplib.OK)
        self.assertTrue(isinstance(res.json(), dict))

    def test_pet_update_endpoint(self):
        petId = self.pet['id']
        res = self.client.post('/pet/{petId}', petId=petId, name='foo',
                               status='bar',
                               format='application/x-www-form-urlencoded')
        self.assertEqual(res.status_code, httplib.OK)

    def test_delete_pet_endpoint(self):
        petId = self.pet['id']
        res = self.client.delete('/pet/{petId}', petId=petId,
                                 auth='special-key')
        self.assertEqual(res.status_code, httplib.OK)
