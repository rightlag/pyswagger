import json
import unittest

from swagger import Swagger


class SwaggerTestCast(unittest.TestCase):
    def setUp(self):
        # Load the schema to create the client object.
        self.client = Swagger.load(
            'http://petstore.swagger.io/v2/swagger.json'
        )
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
                },
            ],
            'status': 'available',
        }

    @property
    def pet(self):
        data = json.dumps(self.data)
        response = self.client.post('/pet', body=data, auth='special-key')
        return response.json()

    def test_swagger_version(self):
        """Assert Swagger version is '2.0'"""
        self.assertEqual(self.client.Version, '2.0')

    def test_create_pet_endpoint(self):
        data = json.dumps(self.data)
        expected_url = 'http://petstore.swagger.io/v2/pet'
        response = self.client.post('/pet', body=data, auth='special-key')
        self.assertEqual(response.url, expected_url)
        self.assertTrue(isinstance(response.json(), dict))
        self.assertEqual(response.status_code, 200)

    def test_get_pet_by_id_endpoint(self):
        petId = self.pet['id']
        response = self.client.get('/pet/{petId}', petId=petId)
        self.assertEqual(response.status_code, 200)

    def test_find_pets_by_status_endpoint(self):
        statuses = ('available', 'pending', 'sold',)
        for status in statuses:
            response = self.client.get('/pet/findByStatus', status=status)
            expected_url = (
                'http://petstore.swagger.io/v2/pet/findByStatus?status={}'
            ).format(status)
            self.assertEqual(response.url, expected_url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(isinstance(response.json(), list))

    def test_find_pet_by_id_endpoint(self):
        petId = self.pet['id']
        response = self.client.get('/pet/{petId}', petId=petId)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.json(), dict))

    def test_pet_update_endpoint(self):
        petId = self.pet['id']
        response = self.client.post(
            '/pet/{petId}', petId=petId, name='foo', status='bar',
            format='application/x-www-form-urlencoded'
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_pet_endpoint(self):
        petId = self.pet['id']
        response = self.client.delete('/pet/{petId}', petId=petId,
                                      auth='special-key')
        self.assertEqual(response.status_code, 200)
