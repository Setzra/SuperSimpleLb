# Super Simple Load Balancer Example
This is a simple load balancer with fake load balancing in order to demonstrate knowledge of what load balancing is and how to achieve (to a point) load balancing while taking a bit into account extendability. 
Could be greatly improved (see [improvements](#improvements))

## Requirements
| tool | version | 
| --- | --- |
| Python | 3.8 (there are likely breaking changes if you use 3.10+) |
| [FastAPI](https://fastapi.tiangolo.com) | 0.74.0 (latest version as of writing) |
| uvicorn | 0.17.5 (used for hosting FastAPI framework) |

# How to install and run
## Installing Python and Dependencies
In case you've never installed Python or haven't updated beyond Python 2 (shame on you), I find the easiest tool to use is [miniconda](https://docs.conda.io/en/latest/miniconda.html), which is basically virtualenv rolled together with a better package manager than pip if you want to use it. The environments miniconda creates are completely isolated and allow for custom Python versions without impacting the system Python installs or other Python projects you may have. 

Assuming you install Conda (on Windows you will need to use the Anaconda Powershell instance):
```bash
conda create -n sample_env python=3.8 # creates a new environment called 'sample_env' and uses Python 3.8
conda activate sample_env # Use your new environment

pip install -r requirements.txt # Install required libraries
```

If you run/manage your own Python installations through some other method like virtualenv, feel free to use that. I only provide the above example for those who may not have had experience with Python.


## Starting the service
Once Python and the service dependencies are installed, you should be able to startup the uvicorn server by simply running the following:

```bash
cd $THE_DIR_THIS_README_IS_IN # Make sure you're in the right place

uvicorn loadbalancer:api --reload
```

This should give output similar to:
```bash
INFO:     Will watch for changes in these directories: ['/mnt/c/Users/setzr/Documents/coding/SimpleLB']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [3835] using watchgod
INFO:     Started server process [3837]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
If you see this, then the service should be up and running. You can verify by visiting http://localhost:8000/docs

## Running and Using the Service
You have 2 UI's to use (these are actually documentation pages, but provide the ability to test/run the service for the sake of example)
* [OpenAPI (used to be called Swagger)](http://localhost:8000/docs) via `/docs`
* [ReDoc](http://localhost:8000/redoc) via `/redoc`

The [service config file](config.json) should be straightforward to figure you. You can modify it and restart the server, or use the UI to modify config and then have it saved to disk for the next time you restart.

| Action | How to do |
| --- | --- |
| List Services | GET at `/services` to get a full list of services being balance, and GET at `/services/{service_name}` to get details on a particular service |
| Add a Service | POST or PUT at `/services/{service_name}` and you should see your service in the list |
| Modify a Service | PUT or PATCH at `/services/{service_name}` which will either overwrite the entire service definition (PUT) or update whatever piece you provide |
| Send a Request to a Service | Use whatever method you'd like at `/{service_name}/{path}` and it will be "load-balanced" around the hosts configured. This assumes you've inputted a path that you list in the service definition.

## Unit Tests
The [unit tests](tests/) are written without any nice framework simply to prevent more dependencies and any possible headaches in getting them to pass. Output is pretty ugly, but the tests work.

To run the tests:
```bash
cd $THE_DIR_THIS_README_IS_IN # Make sure you're in the right place and in the right environment! See install notes above

python -m unittest tests.serviceManagementTests tests.loadBalanceTests
```
This should result in output such as:

```bash

{bunch of gross output}
.
----------------------------------------------------------------------
Ran 15 tests in 0.187s

OK
```

---
## Improvements
* Add healthcheck details, like expected response attributes/codes
* Proper logging instead of prints, integrated with fastAPI and uvicorn's loggers
* Route check for formatting
* Can't have a service called "services", breaks API
* Have a DEFAULT service possible so the service name does not need to be included in routing on the loadbalancer
* Allow wildcard routes to forward many/all routes to healthy hosts
* Dealing with CORS issues that don't exist because this is a simple example
* Add auth to make sure only appropriate parties are accessing API (dependent on design needs)
* Add TLS cert management/usage
* Add extensibility for dictating HTTP method per Route or per Service
* Better service updateablity
* Remove unnecessary models and add in a standard response model