import unittest

import src.routes
from fastapi.testclient import TestClient

client = TestClient(src.routes.api)
src.routes.services = {}  # Get rid of current config

class TestReadWriteServices(unittest.TestCase):

    basicService = {
        'hosts': ['thing1:8080', 'thing2'],
        'routes': ['theCat', '/in/the/hat']   
    }


    def setUp(self):
        # Reset config before each test
        src.routes.services = {}
        return super().setUp()
    

    def test_read_services(self):
        response = client.get('/services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"services": []})


    def test_add_service_via_put(self):
        response = client.put('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.put('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.get('/services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"services": ['someNewThing']})


    def test_add_service_via_post(self):
        response = client.post('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.post('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'Service someNewThing already exists. Overwrite with PUT request or update with PATCH')

        response = client.get('/services')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"services": ['someNewThing']})


    def test_modify_service_host_via_patch(self):
        response = client.post('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.patch('/services/someNewThing', json={'hosts': []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # make sure model was actually updated
        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hosts'], {})

        # Try some other use cases
        response = client.patch('/services/someNewThing', json={'hosts': ['!##$%^&*()']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # make sure model was actually updated and only updated hosts
        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hosts'], {'!##$%^&*()': 'healthy'})
        self.assertEqual(response.json()['routes'], self.basicService['routes'])

        # BAD value
        # Try some other use cases
        response = client.patch('/services/someNewThing', json={'hosts': 'this should be a list'})
        self.assertEqual(response.status_code, 422) # Failed fastAPI parsing/validating

        # make sure model was not updated
        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['hosts'], {'!##$%^&*()': 'healthy'})
        self.assertEqual(response.json()['routes'], self.basicService['routes'])

    
    def test_set_health_on_hosts(self):
        response = client.post('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'name': 'someNewThing', 
            'hosts': {
                'thing1:8080': 'healthy', 
                'thing2': 'healthy'
            }, 
            'routes': ['theCat', '/in/the/hat'], 
            'routing': 'RR', 
            'healthcheck': '/status'
        })

        # Make service sick and check
        response = client.post('/services/someNewThing/thing1:8080?status=300')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'name': 'someNewThing', 
            'hosts': {
                'thing1:8080': 'sick', 
                'thing2': 'healthy'
            }, 
            'routes': ['theCat', '/in/the/hat'], 
            'routing': 'RR', 
            'healthcheck': '/status'
        })

        # Provide miracle cure for server
        response = client.post('/services/someNewThing/thing1:8080?status=200')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'name': 'someNewThing', 
            'hosts': {
                'thing1:8080': 'healthy', 
                'thing2': 'healthy'
            }, 
            'routes': ['theCat', '/in/the/hat'], 
            'routing': 'RR', 
            'healthcheck': '/status'
        })

    
    def test_bad_values_for_health_setting(self):
        response = client.post('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')

        response = client.get('/services/someNewThing')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'name': 'someNewThing', 
            'hosts': {
                'thing1:8080': 'healthy', 
                'thing2': 'healthy'
            }, 
            'routes': ['theCat', '/in/the/hat'], 
            'routing': 'RR', 
            'healthcheck': '/status'
        })

        # non-existent service
        response = client.post('/services/sdklfaklsdjfalskdjfalskdjflkasdjlakdjflkajfalkdf/thing1:8080?status=300')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 'Unknown service sdklfaklsdjfalskdjfalskdjflkasdjlakdjflkajfalkdf')

        # non-existent host
        response = client.post('/services/someNewThing/whoHeardAWhat?status=200')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['status'], 'Unknown host for someNewThing: whoHeardAWhat')

        # bad health status
        response = client.post('/services/someNewThing/thing1:8080?status=-11111')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'I know this is a fake service, but the service code should be between 1 and 600')