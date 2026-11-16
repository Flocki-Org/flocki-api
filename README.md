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

# People, households and groups

People can be stored with a first name, a preferred name, or a last name. Further profile fields, extra email addresses, phone numbers, emergency contacts, categories, service types and custom field values are optional. `PUT /people/` and `PUT` or `PATCH /people/{id}` change only the fields present in the request.

Archiving (`POST /people/{id}/archive`) sets the lifecycle to archived and records the previous status. Restore puts the previous lifecycle back. People are not hard-deleted.

Households keep a required address and a designated leader. A person can belong to a household without leading it. `POST /households/{id}/members` adds a member, `DELETE /households/{id}/members/{person_id}` removes one, and the leader cannot be removed until another member is assigned with `PUT /households/{id}/leader`. Family links are stored once and returned in both directions from `GET /people/{id}/relationships`.

`GET /people` filters in the database. Useful reports live under `/people/upcoming-birthdays`, `/people/upcoming-anniversaries`, `/people/without-email`, `/people/without-mobile`, `/people/without-group` and `/people/inactive`. The older `/peope/with_birthday_before` and `/peope/with_anniversary_before` routes remain.

Categories (`/people/categories`), reference values (`/reference-data`), service types (`/service-types`) and custom fields (`/custom-fields`) are configurable. Custom field definitions apply to an entity type, so the same tables can later hold group fields. Deleting a custom field that already has values deactivates it.

Groups (`/groups`) have categories, a meeting description that can be left empty, and memberships with configurable roles. `GET /people/{id}/groups` lists a person's groups. Deleting a group that still has memberships returns 409 unless `force=true`. Archive and restore are `POST /groups/{id}/archive` and `POST /groups/{id}/restore`.

Departments (`/departments`) are a parent/child tree. People and groups can be linked to a department without the department owning the group.

`POST /imports/elvanto` upserts people, categories, custom fields, households, groups, memberships and custom field values using `external_references`. The same external id updates the existing row. Unknown source fields are stored on the reference. Failures are listed by `GET /imports/errors`. There is no live Elvanto synchronisation.

Schema changes are applied on startup. Revision `001_people_groups_expansion` adds columns and indexes to existing tables and creates the new tables. It does not drop existing people, households or addresses. The recorded version is `schema_migrations`.

OpenAPI examples are on the request models at `/docs`.
