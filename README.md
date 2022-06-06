# Flocki API

This is the backend service for the Flocki church management system. 

## Run app locally
Ensure that you are setup with a Python 3.6+ environment. 
It is recommended to use a virtual environment. To do this, run 
the following command inside this directory:
```
virtualenv venv
```

Activate the virtual environment via:
```
source venv/bin/activate
```

Install all the dependencies via:
```
pip3 install -r requirements.txt
```

Then, to run the app locally, run the following: 
```
python main.py
```

# Run with Docker
## Build docker image locally

To build a docker image, run the following:
```
docker build . -t flocki-api
```

## Run app in docker
After successful build of the image, run the following to expose the api locally on port 8000:

```
docker-compose up -d
```

Check that both the postgres and app containers are running. If they started up successfully you should be able to navigate to the
docs page using the link http://localhost:8000/docs.