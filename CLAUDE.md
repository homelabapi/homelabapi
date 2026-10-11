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
- Pinned to old majors: FastAPI 0.85, Pydantic v1 (`Field(example=...)`, `class Config: schema_extra`), Python 3.10 (`match` statements). Keep Pydantic v1 idioms.

## Architecture

Everything lives in `app/main.py`, in this order:

1. **Config load** (module level): reads `application` (`api_name`, `api_key`, `current_outputs`) and `outputs`. `current_outputs` is a comma-separated string or `"all"`; it becomes a list that `send_output` iterates. Each output key maps to a *list* of accounts, and every sender loops over all of them.
2. **Pydantic models**: `CommonModel` (`api_key`, `subject`, `message`, `url`, `priority`, `source`) plus per-service subclasses whose `schema_extra` examples merge `CommonModel`'s example dict. Sample values come from the `sample_*` constants near the top.
3. **Two kinds of input endpoints:**
   - *Service endpoints* (`/input`, `/healthchecks`, `/monit`, `/smokeping`, `/uptimerobot`): typed JSON body with `api_key` in the body. Each appends its extra fields to `message` as `label: value` lines, then calls `send_output`. `/input` also accepts its fields as URL query parameters when there's no JSON body (the body wins if both are sent); it builds an `InputModel` from them and raises `RequestValidationError` with `query`-prefixed locations on missing fields, so the 422 looks like FastAPI's own query validation errors. It's POST only.
   - *Service webhooks* (`/<service>/{api_key}`): `api_key` in the path, raw `Request` body parsed by hand, because those services' payload formats are fixed.
4. **`send_output(request_body, subject, message, url, priority)`**: dispatches to `send_<output>()` for each entry in `current_outputs`. A failing output (senders raise `SystemExit` on HTTP errors) is caught, logged to stdout with only the output name and exception type (error text can contain token-bearing URLs), and the remaining outputs are still tried. `send_webhook` forwards the request body (service webhooks pass the parsed JSON; typed endpoints pass `payload.dict(exclude={"api_key"})`, after their extra fields have been appended to `message`); the others use subject, message, url, and priority.
5. **`build_message(type, ...)`**: formats the text body per output (Telegram gets HTML `<strong>` subjects, with the subject, message, and url HTML-escaped first because it uses `parse_mode: "HTML"`; email gets raw RFC 822 headers).

Auth is a plain string compare against `app_api_key`. A bad key still returns HTTP 200, with `{"result": "Invalid API Key (401)"}`, and errors inside a handler return 200 with `input_failure` (request validation errors still return FastAPI's 422).

### Adding an input or output

- **Input**: add a `desc_*` (and `subject_*` if needed) constant, a model if it's a typed endpoint, and a route tagged `"Service Endpoints"` or `"Service Webhooks"`. Then update the Supported Inputs list in `README.md`.
- **Output**: add the name to `all_outputs`, a `case` in the config loop and in `send_output`, a `send_<name>()` function, a `build_message` branch if it needs formatting, and a sample block in `config.yaml.sample`. Then update Supported Outputs in `README.md`.

### Known quirks (existing behaviour, not intentional design)

- `send_email` only handles `protocol: "tls"`.

## Releases

- Version lives in `api_version` in `app/main.py`; bump it and add an entry to `CHANGELOG` (plain text, no `.md`, newest first, `vX.Y.Z      YYYY-MM-DD` headings). Past releases did these as separate commits ("Update version number (vA -> vB)", then "Add vX.Y.Z to CHANGELOG").
- `ACR.md` rates the project `B1b` (AI Share 1–25%, Oversight Reviewed). If the AI share of the code or the oversight level changes, update the rating, the `updated` date, and the README badge together.
