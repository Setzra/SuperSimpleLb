# Simple class for some basic backend service
from pydantic import BaseModel
from typing import Optional, List
from fastapi import Request

class BasicServiceModel(BaseModel):
    hosts: List[str]
    routes: List[str]
    healthcheck: Optional[str] = None
    routing: Optional[str] = 'RR'

class BasicServiceModelUpdate(BaseModel):
    hosts: Optional[List[str]]
    routes: Optional[List[str]]
    healthcheck: Optional[str]
    routing: Optional[str]

class BasicService:
    tracker: int = 0

    def __init__(self, name: str, hosts: list = [], routes: list = [], healthcheck: str = '/status', routing = 'RR'):
        self.name = name
        self.routes = routes
        self.routing = routing
        
        self.hosts = {}
        for host in hosts:
            self.hosts[host] = 200

        # This is only here because in reality we'd have a service polling for service health
        # This simple example doesn't actually do that, it's just here because it should be
        self.healthcheck = healthcheck


    def checkHealth(self, host: str):
        return [
            self.hosts[host],
            "healthy" if self.hosts[host] == 200 else "sick" 
        ]

    def setHealth(self, host: str, status: int = 200):
        self.hosts[host] = status

    def addHost(self, host: str):
        # This is just a shortcut to setHealth() since it can already add a service
        # Adding an already existing host simply sets the host to healthy, which is a nice side affect
        self.setHealth(host)

    def removeHost(self, host: str):
        del self.hosts[host]

    def clearHosts(self):
        self.hosts = {}
        self.tracker = 0 # reset track counter as well just to be clean

    def addRoute(self, route: str):
        # Would probably be better to enforce route uniqueness a bit better here
        if route not in self.routes:
            self.routes.append(route)

    def removeRoute(self, route: str):
        self.routes.remove(route)

    def changeHealthcheck(self, healthcheck: str):
        self.healthcheck = healthcheck

    def details(self):
        return {
            'name': self.name,
            'hosts': {host:self.checkHealth(host)[1] for host in self.hosts.keys()},
            'routes': self.routes,
            'routing': self.routing,
            'healthcheck': self.healthcheck
        }

    def dumpConfig(self):
        return {
            'hosts': list(self.hosts.keys()),
            'routes': self.routes,
            'routing': self.routing,
            'healthcheck': self.healthcheck
        }

    # NOTE: This is where the round robin is implemented
    def pickHealthyHost(self):
        healthyHosts = [host for host in self.hosts if self.checkHealth(host)[0] == 200]

        if len(healthyHosts) == 0:
            print('NO HEALTHY HOSTS!!!')
            return None
        
        # This is Round Robin. To add support for other algos, just add more cases here
        if self.routing == 'RR':
            hostIndex = self.tracker % len(healthyHosts)
            self.tracker += 1

            print(f"Healthy hosts: {healthyHosts}, using {healthyHosts[hostIndex]}")
            return healthyHosts[hostIndex]

        else: 
            print('Using unsupported routing mechanism. Currently only Round Robin (RR) is supported')
            return None


    def forwardRequestToBackend(self, route: str, request: Request):
        # We allow both prepending a '/' and not, so check for both
        if route not in self.routes and f"/{route}" not in self.routes:
            return {'status': 404, 'message': f"Route {route} not valid. Routes available: {self.routes}"}

        hostToUse = self.pickHealthyHost()
        route = route if route[:1] != '/' else route[1:]

        if hostToUse is None:
            return {'status': 500, 'message': f"No healthy hosts found for {self.name}. See logs for details"}


        return {'status': 200, 'message': f"Forwarded {request.method} request to http://{hostToUse}/{route}"}


