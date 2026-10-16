# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

HomelabAPI is a self-hosted FastAPI notification hub. Homelab services (Monit, Sonarr, Home Assistant, Tailscale, and so on) POST to it, and it fans each notification out to whichever outputs are configured (Telegram, Pushover, Discord, Matrix, email, and so on). Published as the `homelabapi/homelabapi` Docker image; project site is <https://homelabapi.org>.

## Running

There are no tests, linter config, or build scripts. The app only runs inside Docker as written, because `app/main.py` loads its config from the hard-coded path `/code/app/config.yaml` at import time.

```bash
cp config.yaml.sample config.yaml            # set application.api_key and current_outputs
cp docker-compose.yml.sample docker-compose.yml
docker compose up
```

- `Dockerfile` is excluded via `.git/info/exclude` (not tracked), as are `config.yaml`, `docker-compose.yml`, `test.py`, and `README-PRIVATE.md`. Don't add them to commits; `config.yaml` and `test.py` hold real keys.
- The Dockerfile copies `config.yaml` into the image, and the compose file also bind-mounts it over `/code/app/config.yaml`.
- Swagger UI is served at `/` (custom `templates/index.html`, assets vendored in `assets/`), ReDoc at `/redoc`; `/docs` redirects to `/`.
- Stack: Python 3.14 in the Docker image (the code uses `match`, so 3.10 is the minimum; 3.10 was last checked for v0.10.0), FastAPI, and Pydantic v2. `requirements.txt` pins every installed package (a `pip freeze` of the tested image, plus `exceptiongroup` marked for Python below 3.11), so keep it a full pin list rather than only the direct dependencies. The app sets `strict_content_type=False` on purpose, so a JSON body sent with no Content-Type (as Healthchecks does) is parsed as it was before v0.10.0; don't remove it.

## Architecture

Everything lives in `app/main.py`, in this order:

1. **Config load** (module level): reads `application` (`api_name`, `api_key`, `current_outputs`) and `outputs`. `current_outputs` is a comma-separated string (spaces around names are stripped, empty entries dropped) or `"all"`; it becomes a list that `send_output` iterates. Each output key maps to a *list* of accounts, and every sender loops over all of them.
2. **Pydantic models**: `CommonModel` (`api_key`, `subject`, `message`, `url`, `priority`, `source`) plus per-service subclasses. Each field has its own `Field(examples=[...])` from the `sample_*` constants near the top; they're per field rather than model-level because Pydantic v2 sorts a model-level example's keys, which jumbles the docs. `CommonModel` sets `coerce_numbers_to_str=True` and the optional fields are `Optional[str]`, so numbers (`"priority": 1`) and `null` are accepted as they were under Pydantic v1. `priority` defaults to the int `0`, kept so the outputs get the same value as before.
3. **Two kinds of input endpoints:**
   - *Service endpoints* (`/input`, `/healthchecks`, `/monit`, `/smokeping`, `/uptimerobot`): typed JSON body with `api_key` in the body. Each appends its extra fields to `message` as `label: value` lines, then calls `send_output`. `/input` also accepts its fields as URL query parameters when there's no JSON body (the body wins if both are sent); it builds an `InputModel` from them and raises `RequestValidationError` with `query`-prefixed locations (and `input: None` for a missing parameter) on missing fields, so the 422 looks like FastAPI's own query validation errors. It's POST only.
   - *Service webhooks* (`/<service>/{api_key}`): `api_key` in the path, raw `Request` body parsed by hand, because those services' payload formats are fixed.
4. **`send_output(request_body, subject, message, url, priority)`**: dispatches to `send_<output>()` for each entry in `current_outputs`. A failing output (senders raise `SystemExit` on HTTP errors) is caught, logged to stdout with only the output name and exception type (error text can contain token-bearing URLs), and the remaining outputs are still tried. `send_webhook` forwards the request body (service webhooks pass the parsed JSON; typed endpoints pass `payload.model_dump(exclude={"api_key"}, warnings=False)`, after their extra fields have been appended to `message`; `warnings=False` because the int `priority` default makes Pydantic warn); the others use subject, message, url, and priority. `send_email` takes `protocol` `tls` (STARTTLS), `ssl` (encrypted from the start), or `none`, raises `ValueError` for anything else, and only logs in when `username` is set.
5. **`build_message(type, ...)`**: formats the text body per output (Telegram gets HTML `<strong>` subjects, with the subject, message, and url HTML-escaped first because it uses `parse_mode: "HTML"`; email gets raw RFC 822 headers).

Auth is a plain string compare against `app_api_key`. A bad key returns HTTP 401 via `invalid_api_key()`, with `{"result": "Invalid API Key (401)"}`. Errors inside a handler return 200 with `input_failure`, and request validation errors return FastAPI's 422. Note that `send_output` swallows output failures, so a successful result doesn't mean every output delivered.

### Adding an input or output

- **Input**: add a `desc_*` (and `subject_*` if needed) constant, a model if it's a typed endpoint, and a route tagged `"Service Endpoints"` or `"Service Webhooks"`. Then update the Supported Inputs list in `README.md`.
- **Output**: add the name to `all_outputs`, a `case` in the config loop and in `send_output`, a `send_<name>()` function, a `build_message` branch if it needs formatting, and a sample block in `config.yaml.sample`. Then update Supported Outputs in `README.md`.

## Releases

- Version lives in `api_version` in `app/main.py`; bump it and add an entry to `CHANGELOG` (plain text, no `.md`, newest first, `vX.Y.Z      YYYY-MM-DD` headings). Since v0.8.0, the version bump and the CHANGELOG entry go in the same commit as the change they release (releases before that used separate commits). Tag the release commit `vX.Y.Z`.
- `ACR.md` rates the project `B1b` (AI Share 1–25%, Oversight Reviewed). If the AI share of the code or the oversight level changes, update the rating, the `updated` date, and the README badge together.
