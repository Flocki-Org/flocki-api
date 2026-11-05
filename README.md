# Flocki API

This is the backend service for the Flocki church management system. 

## Run app locally
Ensure that you are setup with a Python 3.15 environment. 
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

Then, to run tests, run:
```
python -m pytest
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

# Deploy on Render

The API expects Postgres connection settings via environment variables.

**Recommended (Render-linked database):** set a single URL — either `DATABASE_URL` or `FLOCKI_API_DATABASE_URL` — to the connection string from the database **Connect** menu. Prefer the **Internal** URL when the web service and database are in the **same region**; otherwise use the **External** URL.

**Component settings (also supported):**

| Variable | Purpose |
| --- | --- |
| `FLOCKI_API_DB_HOST` | Hostname. Use the full External host (`dpg-….region-postgres.render.com`) if Internal DNS fails |
| `FLOCKI_API_DB_PORT` | Port (default `5432`) |
| `FLOCKI_API_DB_USER_NAME` | Database user |
| `FLOCKI_API_DB_PASSWORD` | Database password |
| `FLOCKI_API_DB_NAME` | Database name |
| `FLOCKI_API_DB_RENDER_REGION` | e.g. `oregon` — used to expand a bare Internal host (`dpg-…-a`) when it does not resolve |
| `FLOCKI_API_DB_SSLMODE` | Defaults to `require` for `*.render.com` hosts |

If deploy logs show `could not translate host name "dpg-…-a"`, the web service cannot resolve the Internal hostname (almost always a **region mismatch**). Fix by aligning regions, or switch the host/URL to the External connection string. A `render.yaml` Blueprint is included that places the web service and database in `oregon` together.

Health check path: `/healthz`.