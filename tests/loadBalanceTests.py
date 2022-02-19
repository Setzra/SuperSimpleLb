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

        response = client.put('/services/someNewThing', json=self.basicService)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.json()['details']['name'], 'someNewThing')
        
        return super().setUp()

    
    def test_simple_http_methods(self):
        httpActions = ['get', 'post', 'put', 'delete', 'head', 'options', 'patch'] # 'trace' is not supported by the test client
        for action in httpActions:
            response = getattr(client, action)('/someNewThing/theCat')
            self.assertEqual(response.status_code, 200)

    
    def test_non_existent_service(self):
        response = client.get('/someOldThing/in/the/hat')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Unknown service someOldThing')


    def test_non_existent_path(self):
        response = client.get('/someNewThing/the/grinch/hates')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], "Route the/grinch/hates not valid. Routes available: ['theCat', '/in/the/hat']")

    
    def test_round_robin_2_servers_healthy(self):
        # Should go to 1st server in list and DOES NOT include the service name
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

        # Should go to 1st server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')


    def test_round_robin_2_servers_1_unhealthy(self):
        response = client.post('/services/someNewThing/thing2?status=24')
        self.assertEqual(response.status_code, 200)

        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 1st server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # healing the server should add it back in
        response = client.post('/services/someNewThing/thing2?status=200')
        self.assertEqual(response.status_code, 200)

        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

    
    def test_round_robin_2_servers_unhealthy(self):
        response = client.post('/services/someNewThing/thing2?status=111')
        self.assertEqual(response.status_code, 200)
        response = client.post('/services/someNewThing/thing1:8080?status=112')
        self.assertEqual(response.status_code, 200)

        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['message'], 'No healthy hosts found for someNewThing. See logs for details')

    
    def test_no_hosts_at_all(self):
        response = client.patch('/services/someNewThing', json={'hosts':[]})
        self.assertEqual(response.status_code, 200)

        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['message'], 'No healthy hosts found for someNewThing. See logs for details')


    def test_adding_hosts_should_get_used(self):
        # Should go to 1st server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

        # Should go back to first
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Adding a server should get used
        response = client.patch('/services/someNewThing', json={'hosts': self.basicService['hosts'] + ['newHost']})
        self.assertEqual(response.status_code, 200)

        # Should go to 1st server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

        # Should go to 3rd server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://newHost/in/the/hat')


    def test_removing_next_rr_host_should_not_break(self):
        # Adding a server should get used
        response = client.patch('/services/someNewThing', json={'hosts': self.basicService['hosts'] + ['newHost']})
        self.assertEqual(response.status_code, 200)

        # Should go to 1st server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing1:8080/in/the/hat')

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

        # Should go to 3rd server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://newHost/in/the/hat')

        # Adding a server should get used
        response = client.patch('/services/someNewThing', json={'hosts': ['thing2', 'newHost']})
        self.assertEqual(response.status_code, 200)

        # Should go to 2nd server in list
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://thing2/in/the/hat')

        # Should go to newHost server
        response = client.get('/someNewThing/in/the/hat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Forwarded GET request to http://newHost/in/the/hat')