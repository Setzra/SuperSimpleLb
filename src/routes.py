import json
import os
import time
import shutil

from typing import Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse as response

from .service import BasicService, BasicServiceModel, BasicServiceModelUpdate

# Check if config file exists. Create a blank one if not
configFileLoc = os.path.join(os.getcwd(), 'config.json')
if not os.path.exists(configFileLoc):
    with open(configFileLoc, 'w') as config:
        config.write('{}')


# Startup API
api = FastAPI(
    title="Basic Service LoadBalancer",
    description="Just a simple api for adding, removing, and load balancing services and routes for those services",
    version="0.0.1 pre-Alpha mk XVII"
)
namespaceTags = [
    {
        'name': 'SimpleLB Management',
        'description': 'Just a simple load balancing example API'
    },
    {
        'name': 'Service Forwarding',
        'description': 'Forward a particular request to a particular service backend'
    }
]

services: Dict[str, BasicService] = {}

# Simple helper function for loading a service into our management dict
def loadService(name, details):
    services[name] = BasicService(name, details['hosts'], details['routes'])
        
    if details['healthcheck'] is not None:
        services[name].changeHealthcheck(details['healthcheck'])


# Load our starting config
try:
    with open(configFileLoc, 'r') as config:
        startingServices = json.load(config)

        for name, details in startingServices.items():
            print(f"\nLoading {name} with details: {details}")
            loadService(name, details)

except:
    print("ERROR LOADING CONFIG. SKIPPING!")

###############################################################################
# Route definitions for managing services
###############################################################################

@api.get("/services", tags=['SimpleLB Management'])
def get_services():
    '''Get the list of available services'''
    return response({'services': list(services.keys())})


@api.post("/services/save", tags=['SimpleLB Management'])
def save_current_services_to_config():
    '''Saves the current list of services to config for easier startup next time'''

    # Backup current config
    shutil.copyfile(configFileLoc, f"{configFileLoc}.{time.time_ns()}")

    with open(configFileLoc, 'w') as config:
        jsonToDump = {serviceName:service.dumpConfig() for (serviceName, service) in services.items()}
        config.write(json.dumps(jsonToDump, indent=2))

    return response({'message': 'success'})


@api.get("/services/{serviceName}", tags=['SimpleLB Management'])
def get_service_details(serviceName: str):
    '''Get the details for a particular service'''
    return response(services[serviceName].details())


@api.post("/services/{serviceName}", tags=['SimpleLB Management'])
def create_new_service(serviceName: str, serviceDetails: BasicServiceModel):
    '''Provide details of a **NEW** service'''

    if serviceName in services.keys():
        return response({"status": f"Service {serviceName} already exists. Overwrite with PUT request or update with PATCH"}, status_code=400)
    
    print(f"Creating new service {serviceName} with details: {serviceDetails}")
    loadService(serviceName, serviceDetails.dict())

    return response({"status": "success", "details": {"name": serviceName, **serviceDetails.dict()}})


@api.patch("/services/{serviceName}", tags=['SimpleLB Management'])
def update_an_existing_service(serviceName: str, serviceDetails: BasicServiceModelUpdate):
    '''Update service details for an existing service'''

    if serviceName not in services.keys():
        return response({"status": f"Service {serviceName} does not exist. Please run PUT or POST to create this service"}, status_code=404)
    
    print(f"Updating service {serviceName} with details: {serviceDetails}")
    
    whatToUpdate = serviceDetails.dict()
    serviceToUpdate = services[serviceName]
    
    for key, value in whatToUpdate.items():
        # Might be better to look for dynamic JSON merging/python object updater
        if value is None:
            continue
        
        elif key == 'hosts':
            serviceToUpdate.clearHosts()
            for host in value:
                serviceToUpdate.addHost(host)

        # This is quick and dirty and generally bad. Only here for simplicity in implementation
        elif hasattr(serviceToUpdate, key):
            setattr(serviceToUpdate, key, value)

    return response({"status": "success", "details": serviceToUpdate.details()})


@api.put("/services/{serviceName}", tags=['SimpleLB Management'])
def create_or_override_service(serviceName: str, serviceDetails: BasicServiceModel):
    '''Provide details of a new service to add **OR** override the details for an existing service'''
    
    print(f"Creating new service {serviceName} with details: {serviceDetails}")
    loadService(serviceName, serviceDetails.dict())

    return response({"status": "success", "details": {"name": serviceName, **serviceDetails.dict()}})


@api.post("/services/{serviceName}/{host}", tags=['SimpleLB Management'])
def set_host_healtcheck_status_for_service(serviceName: str, host: str, status: int = 200):
    '''Set the current HTTP status for a particular host in a particular service'''

    # These validations can be done directly by fastAPI via param validation above, I only put it here for easier readability
    # In a production system I'd rather integrate this right into the built in validator for speed/simplicity
    if serviceName not in services.keys():
        return response({"status": f"Unknown service {serviceName}"}, status_code=404)
    
    if host not in services[serviceName].hosts:
        return response({"status": f"Unknown host for {serviceName}: {host}"}, status_code=404)

    if status < 1 or status > 599:
        return response({"status": f"I know this is a fake service, but the service code should be between 1 and 600"}, status_code=400)

    services[serviceName].setHealth(host, status)

    return response({"status": "success", "details": {"host": host, "status": status}})


###############################################################################
# Route definitions for testing the loadbalancing of backend services
# NOTE: The body of the request does not appear in the "docs" UI, but is passed
# on via the "request" parameter
###############################################################################
@api.get(       '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.put(       '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.post(      '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.delete(    '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.head(      '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.options(   '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.patch(     '/{serviceName}/{route:path}', tags=['Service Forwarding'])
@api.trace(     '/{serviceName}/{route:path}', tags=['Service Forwarding'])
def forward_a_request_to_a_particular_service(serviceName: str, route: str, request: Request):
    '''Forwards the request on to the backend service, where an appropriate host with be chosen'''
    if serviceName not in services.keys():
        return response({"status": 404, "message": f"Unknown service {serviceName}"}, status_code=404)

    forwardingResult = services[serviceName].forwardRequestToBackend(route, request)
    return response({"status": forwardingResult['status'], "message": forwardingResult['message']}, status_code=forwardingResult['status'])

    