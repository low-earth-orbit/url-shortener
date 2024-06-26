# CS3103 Term Project, Group N: URL Shortener

The URL (link) shortener enables registered users to add/remove shortened URLs and anyone with the shortcut can retrieve the full URL.

## Tech stack

- Frontend: HTML, CSS, JavaScript, Bootstrap, Vue.js
- API: OpenAPI Specification, Python, Flask
- Database: MariaDB

## UI

![UI](/ui.png "User interface of the app")

## User Stories

A registered user can

- Sign in & sign out, using the FCS LDAP server for authentication
- Manage user shortcuts (view and delete)
- Create a shortcut under this user by providing a long URL

An anonymous user can

- Create a shortcut by providing a long URL

Anyone with a short link can

- Use the shortcut to visit the destination URL

## File References

Database Design: [`/db-design.md`](/db-design.md)

SQL scripts: [`/db-creation.sql`](/db-creation.sql)

API doc (webpage): [`/app/static/api.html`](/app/static/api.html)

API doc (yaml): [`/api.yaml`](/api.yaml)

Happy path tests: [`/api-happy-path.sh`](/api-happy-path.sh)

Unhappy path tests: [`/api-unhappy-path.sh`](/api-unhappy-path.sh)

App folder: [`/app`](/app)

API server: [`/app/app.py`](/app/app.py)

Static file directory: [`/app/static`](/app/static)
