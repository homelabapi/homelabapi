import json
import requests
import smtplib
import ssl
import uuid
import yaml
from fastapi import FastAPI, Request, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

all_outputs = (
    "discord",
    "email",
    "gotify",
    "matrix",
    "ntfysh",
    "pushbullet",
    "pushover",
    "telegram",
    "webhook",
)

with open("/code/app/config.yaml", mode="rt", encoding="utf-8") as file:
    configuration = yaml.safe_load(file)

    app_settings = configuration["application"]
    for key, value in app_settings.items():
        match key:
            case "api_name":
                api_title = value
            case "api_key":
                app_api_key = value
            case "current_outputs":
                if "," in value:
                    current_outputs = value.split(",")
                else:
                    if value == "all":
                        current_outputs = all_outputs
                    else:
                        current_outputs = [value]

    outputs = {}
    output_settings = configuration["outputs"]
    for key, value in output_settings.items():
        match key:
            case "discord":
                outputs["discord"] = value
            case "email":
                outputs["email"] = value
            case "gotify":
                outputs["gotify"] = value
            case "matrix":
                outputs["matrix"] = value
            case "ntfysh":
                outputs["ntfysh"] = value
            case "pushbullet":
                outputs["pushbullet"] = value
            case "pushover":
                outputs["pushover"] = value
            case "telegram":
                outputs["telegram"] = value
            case "webhook":
                outputs["webhook"] = value

app_dir = "app"
api_version = "0.6.1"

api_description = "Welcome to " + api_title + "."
input_success = "Success! Your input request was accepted by " + api_title
input_failure = "Failure! Your input request was NOT accepted by " + api_title

# Endpoint Descriptions
desc_healthchecks = "Receive a POST request from HealthChecks"
desc_input = "This is the default POST endpoint. This endpoint should be used if none of the service-specific endpoints or webhooks apply."
desc_monit = "Receive a POST request from Monit"
desc_smokeping = "Receive a POST request from SmokePing"
desc_uptimerobot = "Receive a POST request from UptimeRobot"

# Webhook Descriptions
desc_changedetectionio = "Receive a webhook from ChangeDetection.io"
desc_headphones = "Receive a webhook from Headphones"
desc_homeassistant = "Receive a webhook from Home Assistant"
desc_lazylibrarian = "Receive a webhook from LazyLibrarian"
desc_radarr = "Receive a webhook from Radarr"
desc_sonarr = "Receive a webhook from Sonarr"
desc_synology = "Receive a webhook from a Synology NAS"
desc_tailscale = "Receive a webhook from Tailscale"

# Default Subjects
subject_changedetectionio = "ChangeDetection.io"
subject_headphones = "Headphones"
subject_homeassistant = "Home Assistant"
subject_lazylibrarian = "LazyLibrarian"
subject_monit = "Monit"
subject_radarr = "Radarr"
subject_sonarr = "Sonarr"
subject_synology = "NAS"
subject_tailscale = "Tailscale"

# Sample Common Values
sample_api_key = "abc123def456ghi789j0abc123def456ghi789j0"
sample_subject = "Output (" + api_title + ")"
sample_message = "This is a sample message."
sample_url = "https://example.com"
sample_priority = "1"
sample_source = "Service Name"

# Sample HealthChecks Values
sample_healthchecks_name = "$NAME"
sample_healthchecks_status = "$STATUS"
sample_healthchecks_tags = "$TAGS"
sample_healthchecks_time = "$NOW"
sample_healthchecks_uuid = "$CODE"

# Sample Monit Values
sample_monit_action = "n/a"
sample_monit_date = "Sun, 18 Dec 20222 19:22:25"
sample_monit_description = (
    "cpu usage of 99.7% matches resource limit [cpu usage > 80.0%]"
)
sample_monit_event = "Resource limit matched"
sample_monit_host = "email.example.com"
sample_monit_process_children = "xxx"
sample_monit_process_cpu_percent = "xxx"
sample_monit_process_pid = "xxx"
sample_monit_process_memory = "xxx"
sample_monit_program_status = "xxx"
sample_monit_service = "ssh"

# Sample SmokePing Values
sample_smokeping_alertname = "hostdown"
sample_smokeping_hostname = "127.0.0.1"
sample_smokeping_losspattern = "loss: 100%"
sample_smokeping_target = "MyServerName"
sample_smokeping_rtt = "U"

# Sample UptimeRobot Values
sample_uptimerobot_adt = "*alertDateTime*"
sample_uptimerobot_ade = "*alertDetails*"
sample_uptimerobot_adu = "*alertDuration*"
sample_uptimerobot_at = "*alertType*"
sample_uptimerobot_atfn = "*alertTypeFriendlyName*"
sample_uptimerobot_mac = "*monitorAlertContacts*"
sample_uptimerobot_mfn = "*monitorFriendlyName*"
sample_uptimerobot_mid = "*monitorID*"
sample_uptimerobot_murl = "*monitorURL*"
sample_uptimerobot_sed = "*sslExpiryDate*"
sample_uptimerobot_sedl = "*sslExpiryDaysLeft*"

tags_metadata = [
    {
        "name": "Default Endpoint",
        "description": "",
    },
    {
        "name": "Service Endpoints",
        "description": "",
    },
    {
        "name": "Service Webhooks",
        "description": "",
    },
]


class CommonModel(BaseModel):
    api_key: str = Field(example=sample_api_key)
    subject: str = Field(default=sample_subject, example=sample_subject)
    message: str = Field(example=sample_message)
    url: str = Field(default=None, example=sample_url)
    priority: str = Field(default=0, example=sample_priority)
    source: str = Field(default=None, example=sample_source)

    class Config:
        schema_extra = {
            "example": {
                "api_key": sample_api_key,
                "subject": sample_subject,
                "message": sample_message,
                "url": sample_url,
                "priority": sample_priority,
                "source": sample_source,
            }
        }


class InputModel(CommonModel):
    pass


class HealthChecksModel(CommonModel):
    name: str = Field(default=None, example=sample_healthchecks_name)
    status: str = Field(default=None, example=sample_healthchecks_status)
    tags: str = Field(default=None, example=sample_healthchecks_tags)
    time: str = Field(default=None, example=sample_healthchecks_time)
    uuid: str = Field(default=None, example=sample_healthchecks_uuid)

    class Config:
        schema_extra = dict(
            {
                "example": {
                    **CommonModel.Config.schema_extra["example"],
                    **{"name": sample_healthchecks_name},
                    **{"status": sample_healthchecks_status},
                    **{"tags": sample_healthchecks_tags},
                    **{"time": sample_healthchecks_time},
                    **{"uuid": sample_healthchecks_uuid},
                }
            }
        )


class MonitModel(CommonModel):
    action: str = Field(default=None, example=sample_monit_action)
    date: str = Field(default=None, example=sample_monit_date)
    description: str = Field(default=None, example=sample_monit_description)
    event: str = Field(default=None, example=sample_monit_event)
    host: str = Field(default=None, example=sample_monit_host)
    process_children: str = Field(default=None, example=sample_monit_process_children)
    process_cpu_percent: str = Field(
        default=None, example=sample_monit_process_cpu_percent
    )
    process_pid: str = Field(default=None, example=sample_monit_process_pid)
    process_memory: str = Field(default=None, example=sample_monit_process_memory)
    program_status: str = Field(default=None, example=sample_monit_program_status)
    service: str = Field(default=None, example=sample_monit_service)

    class Config:
        schema_extra = {
            "example": {
                **CommonModel.Config.schema_extra["example"],
                "action": sample_monit_action,
                "date": sample_monit_date,
                "description": sample_monit_description,
                "event": sample_monit_event,
                "host": sample_monit_host,
                "process_children": sample_monit_process_children,
                "process_cpu_percent": sample_monit_process_cpu_percent,
                "process_pid": sample_monit_process_pid,
                "process_memory": sample_monit_process_memory,
                "program_status": sample_monit_program_status,
                "service": sample_monit_service,
            }
        }


class SmokePingModel(CommonModel):
    alertname: str = Field(default=None, example=sample_smokeping_alertname)
    hostname: str = Field(default=None, example=sample_smokeping_hostname)
    losspattern: str = Field(default=None, example=sample_smokeping_losspattern)
    rtt: str = Field(default=None, example=sample_smokeping_rtt)
    target: str = Field(default=None, example=sample_smokeping_target)

    class Config:
        schema_extra = dict(
            {
                "example": {
                    **CommonModel.Config.schema_extra["example"],
                    **{"alertname": sample_smokeping_alertname},
                    **{"hostname": sample_smokeping_hostname},
                    **{"losspattern": sample_smokeping_losspattern},
                    **{"rtt": sample_smokeping_rtt},
                    **{"target": sample_smokeping_target},
                }
            }
        )


class UptimeRobotModel(CommonModel):
    alertDateTime: str = Field(default=None, example=sample_uptimerobot_adt)
    alertDetails: str = Field(default=None, example=sample_uptimerobot_ade)
    alertDuration: str = Field(default=None, example=sample_uptimerobot_adu)
    alertType: str = Field(default=None, example=sample_uptimerobot_at)
    alertTypeFriendlyName: str = Field(default=None, example=sample_uptimerobot_atfn)
    monitorAlertContacts: str = Field(default=None, example=sample_uptimerobot_mac)
    monitorFriendlyName: str = Field(default=None, example=sample_uptimerobot_mfn)
    monitorID: str = Field(default=None, example=sample_uptimerobot_mid)
    monitorURL: str = Field(default=None, example=sample_uptimerobot_murl)
    sslExpiryDate: str = Field(default=None, example=sample_uptimerobot_sed)
    sslExpiryDaysLeft: str = Field(default=None, example=sample_uptimerobot_sedl)

    class Config:
        schema_extra = dict(
            {
                "example": {
                    **CommonModel.Config.schema_extra["example"],
                    **{"alertDateTime": sample_uptimerobot_adt},
                    **{"alertDetails": sample_uptimerobot_ade},
                    **{"alertDuration": sample_uptimerobot_adu},
                    **{"alertType": sample_uptimerobot_at},
                    **{"alertTypeFriendlyName": sample_uptimerobot_atfn},
                    **{"monitorAlertContacts": sample_uptimerobot_mac},
                    **{"monitorFriendlyName": sample_uptimerobot_mfn},
                    **{"monitorID": sample_uptimerobot_mid},
                    **{"monitorURL": sample_uptimerobot_murl},
                    **{"sslExpiryDate": sample_uptimerobot_sed},
                    **{"sslExpiryDaysLeft": sample_uptimerobot_sedl},
                }
            }
        )


app = FastAPI(
    version="v" + api_version,
    title=api_title,
    description=api_description,
    docs_url=None,
    redoc_url=None,
    openapi_tags=tags_metadata,
    swagger_ui_default_parameters={
        "dom_id": "#swagger-ui",
        "layout": "BaseLayout",
        "deepLinking": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

templates = Jinja2Templates(directory="templates")


@app.head(
    "/",
    tags=["Documentation"],
    summary="This is here for services that ping the API using HEAD, such as UptimeRobot.",
    description="This is here for services that ping the API using HEAD, such as UptimeRobot.",
    include_in_schema=False,
)
@app.get(
    "/",
    tags=["Documentation"],
    summary="Displays the primary documentation (OpenAPI/Swagger) -- You're viewing this right now!",
    description="Displays the primary documentation (OpenAPI/Swagger) -- You're viewing this right now!",
    include_in_schema=False,
)
async def show_docs(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "api_title": api_title}
    )


@app.get(
    "/docs",
    tags=["Documentation"],
    summary="Redirects to /",
    description="Redirects to /",
    include_in_schema=False,
)
def redirect_docs():
    response = RedirectResponse(url="/")
    return response


@app.get(
    "/redoc",
    tags=["Documentation"],
    summary="Displays the alternate documentation (Redoc)",
    description="Displays the alternate documentation (Redoc)",
    include_in_schema=False,
)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=api_title,
        redoc_js_url="/assets/redoc.standalone.js",
        redoc_favicon_url="/assets/favicon.png",
    )


@app.get(
    app.swagger_ui_oauth2_redirect_url,
    tags=["System"],
    summary="OAuth redirect thingie",
    description="OAuth redirect thingie",
    include_in_schema=False,
)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.post(
    "/input",
    summary=desc_input,
    description=desc_input,
    tags=["Default Endpoint"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def default_input(payload: InputModel):

    if payload.api_key == app_api_key:

        try:

            send_output(
                payload.json,
                payload.subject,
                payload.message,
                payload.url,
                payload.priority,
            )
            to_return = {"result": input_success}

        except Exception:

            to_return = {"result": input_failure}

        return to_return

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/healthchecks",
    summary=desc_healthchecks,
    description=desc_healthchecks,
    tags=["Service Endpoints"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
def healthchecks(payload: HealthChecksModel):

    if payload.api_key == app_api_key:

        try:
            payload.message += "\n\n"

            try:
                if payload.url and payload.url != "":
                    payload.message += payload.url + "\n\n"
                    payload.url = ""
            except:
                pass

            try:
                if payload.name and payload.name != "":
                    payload.message += "Name: " + payload.name + "\n"
            except:
                pass

            try:
                if payload.status and payload.status != "":
                    payload.message += "Status: " + payload.status + "\n"
            except:
                pass

            try:
                if payload.tags and payload.tags != "":
                    payload.message += "Tags: " + payload.tags + "\n"
            except:
                pass

            try:
                if payload.time and payload.time != "":
                    payload.message += "Time: " + payload.time + "\n"
            except:
                pass

            try:
                if payload.uuid and payload.uuid != "":
                    payload.message += "UUID: " + payload.uuid + "\n"
            except:
                pass

            send_output(
                payload.json(),
                payload.subject,
                payload.message,
                payload.url,
                payload.priority,
            )
            to_return = {"result": input_success}

        except Exception:

            to_return = {"result": input_failure}

        return to_return

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/monit",
    summary=desc_monit,
    description=desc_monit,
    tags=["Service Endpoints"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def monit(payload: MonitModel):

    if payload.api_key == app_api_key:

        try:

            payload.message += "\n\n"

            try:
                if payload.action and payload.action != "":
                    payload.message += "action: " + payload.action + "\n"
            except:
                pass

            try:
                if payload.date and payload.date != "":
                    payload.message += "date: " + payload.date + "\n"
            except:
                pass

            try:
                if payload.description and payload.description != "":
                    payload.message += "description: " + payload.description + "\n"
            except:
                pass

            try:
                if payload.event and payload.event != "":
                    payload.message += "event: " + payload.event + "\n"
            except:
                pass

            try:
                if payload.host and payload.host != "":
                    payload.message += "host: " + payload.host + "\n"
            except:
                pass

            try:
                if payload.process_children and payload.process_children != "":
                    payload.message += (
                        "process_children: " + payload.process_children + "\n"
                    )
            except:
                pass

            try:
                if payload.process_cpu_percent and payload.process_cpu_percent != "":
                    payload.message += (
                        "process_cpu_percent: " + payload.process_cpu_percent + "\n"
                    )
            except:
                pass

            try:
                if payload.process_pid and payload.process_pid != "":
                    payload.message += "process_pid: " + payload.process_pid + "\n"
            except:
                pass

            try:
                if payload.process_memory and payload.process_memory != "":
                    payload.message += (
                        "process_memory: " + payload.process_memory + "\n"
                    )
            except:
                pass

            try:
                if payload.program_status and payload.program_status != "":
                    payload.message += (
                        "program_status: " + payload.program_status + "\n"
                    )
            except:
                pass

            try:
                if payload.service and payload.service != "":
                    payload.message += "service: " + payload.service + "\n"
            except:
                pass

            send_output(payload.json(), payload.subject, payload.message, "", "")
            to_return = {"result": input_success}

        except Exception:

            to_return = {"result": input_failure}

        return to_return

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/smokeping",
    summary=desc_smokeping,
    description=desc_smokeping,
    tags=["Service Endpoints"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
def smokeping(payload: SmokePingModel):

    if payload.api_key == app_api_key:

        try:
            payload.message += "\n\n"

            try:
                if payload.url and payload.url != "":
                    payload.message += payload.url + "\n\n"
                    payload.url = ""
            except:
                pass

            try:
                if payload.alertname and payload.alertname != "":
                    payload.message += "Alert Name: " + payload.alertname + "\n"
            except:
                pass

            try:
                if payload.hostname and payload.hostname != "":
                    payload.message += "Hostname: " + payload.hostname + "\n"
            except:
                pass

            try:
                if payload.losspattern and payload.losspattern != "":
                    payload.message += "Loss Pattern: " + payload.losspattern + "\n"
            except:
                pass

            try:
                if payload.rtt and payload.rtt != "":
                    payload.message += "RTT: " + payload.rtt + "\n"
            except:
                pass

            try:
                if payload.target and payload.target != "":
                    payload.message += "Target: " + payload.target + "\n"
            except:
                pass

            send_output(
                payload.json(),
                payload.subject,
                payload.message,
                payload.url,
                payload.priority,
            )
            to_return = {"result": input_success}

        except Exception:

            to_return = {"result": input_failure}

        return to_return

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/uptimerobot",
    summary=desc_uptimerobot,
    description=desc_uptimerobot,
    tags=["Service Endpoints"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def uptimerobot(payload: UptimeRobotModel):

    if payload.api_key == app_api_key:

        try:

            payload.message += "\n\n"

            try:
                if payload.url and payload.url != "":
                    payload.message += payload.url + "\n\n"
                    payload.url = ""
            except:
                pass

            try:
                if payload.alertDateTime and payload.alertDateTime != "*alertDateTime*":
                    payload.message += "alertDateTime: " + payload.alertDateTime + "\n"
            except:
                pass

            try:
                if payload.alertDetails and payload.alertDetails != "*alertDetails*":
                    payload.message += "alertDetails: " + payload.alertDetails + "\n"
            except:
                pass

            try:
                if payload.alertDuration and payload.alertDuration != "*alertDuration*":
                    payload.message += "alertDuration: " + payload.alertDuration + "\n"
            except:
                pass

            try:
                if payload.alertType and payload.alertType != "*alertType*":
                    payload.message += "alertType: " + payload.alertType + "\n"
            except:
                pass

            try:
                if (
                    payload.alertTypeFriendlyName
                    and payload.alertTypeFriendlyName != "*alertTypeFriendlyName*"
                ):
                    payload.message += (
                        "alertTypeFriendlyName: " + payload.alertTypeFriendlyName + "\n"
                    )
            except:
                pass

            try:
                if (
                    payload.monitorAlertContacts
                    and payload.monitorAlertContacts != "*monitorAlertContacts*"
                ):
                    payload.message += (
                        "monitorAlertContacts: " + payload.monitorAlertContacts + "\n"
                    )
            except:
                pass

            try:
                if (
                    payload.monitorFriendlyName
                    and payload.monitorFriendlyName != "*monitorFriendlyName*"
                ):
                    payload.message += (
                        "monitorFriendlyName: " + payload.monitorFriendlyName + "\n"
                    )
            except:
                pass

            try:
                if payload.monitorID and payload.monitorID != "*monitorID*":
                    payload.message += "monitorID: " + payload.monitorID + "\n"
            except:
                pass

            try:
                if payload.monitorURL and payload.monitorURL != "*monitorURL*":
                    payload.message += "monitorURL: " + payload.monitorURL + "\n"
            except:
                pass

            try:
                if payload.sslExpiryDate and payload.sslExpiryDate != "*sslExpiryDate*":
                    payload.message += "sslExpiryDate: " + payload.sslExpiryDate + "\n"
            except:
                pass

            try:
                if (
                    payload.sslExpiryDaysLeft
                    and payload.sslExpiryDaysLeft != "*sslExpiryDaysLeft*"
                ):
                    payload.message += (
                        "sslExpiryDaysLeft: " + payload.sslExpiryDaysLeft + "\n"
                    )
            except:
                pass

            send_output(
                payload.json(),
                payload.subject,
                payload.message,
                payload.url,
                payload.priority,
            )
            to_return = {"result": input_success}

        except Exception:

            to_return = {"result": input_failure}

        return to_return

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/changedetectionio/{api_key}",
    summary=desc_changedetectionio,
    description=desc_changedetectionio,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_changedetectionio(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            send_output(
                result,
                result["title"],
                result["message"].removesuffix("\n---\n\n---"),
                "",
                0,
            )
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/headphones/{api_key}",
    summary=desc_headphones,
    description=desc_headphones,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_headphones(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            send_output(result, subject_headphones, result["text"], "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/homeassistant/{api_key}",
    summary=desc_homeassistant,
    description=desc_homeassistant,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_homeassistant(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            send_output(result, subject_homeassistant, result["text"], "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/lazylibrarian/{api_key}",
    summary=desc_lazylibrarian,
    description=desc_lazylibrarian,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_lazylibrarian(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            send_output(result, subject_lazylibrarian, result["text"], "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/radarr/{api_key}",
    summary=desc_radarr,
    description=desc_radarr,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_radarr(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            full_message = (
                str(result["movie"]["title"])
                + " ["
                + str(result["movie"]["year"])
                + "]"
            )
            send_output(result, subject_radarr, full_message, "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/sonarr/{api_key}",
    summary=desc_sonarr,
    description=desc_sonarr,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_sonarr(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()

            subject_end = ""
            match result["eventType"]:
                case "Backup":
                    subject_end = " -- Episode Backed Up"
                case "Corrupt":
                    subject_end = " -- Episode Corrupted"
                case "Deleted":
                    subject_end = " -- Episode Deleted"
                case "Download":
                    subject_end = " -- Episode Downloaded"
                case "Event":
                    subject_end = " -- Event"
                case "Failed":
                    subject_end = " -- Corrupted"
                case "Grab":
                    subject_end = " -- Grabbed"
                case "Health":
                    subject_end = " -- Health Issues"
                case "Test":
                    subject_end = " -- Test"
                case "Update":
                    subject_end = " -- Updated"
                case "Upgrade":
                    subject_end = " -- Upgraded"
            full_subject = subject_sonarr + subject_end

            # The Sonarr test notification doesn't include an air date, in which case a default value needs to be set
            try:

                air_date = result["episodes"][0]["airDate"]

            except:

                air_date = "unknown air date"

            full_message = (
                str(result["eventType"])
                + "\n\n"
                + str(result["series"]["title"])
                + " - "
                + str(result["episodes"][0]["seasonNumber"])
                + "x"
                + str(result["episodes"][0]["episodeNumber"])
                + " - "
                + str(result["episodes"][0]["title"])
                + " ["
                + str(air_date)
                + "]"
            )

            send_output(result, full_subject, full_message, "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/synology/{api_key}",
    summary=desc_synology,
    description=desc_synology,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_synology(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()
            send_output(result, subject_synology, result["message"], "", 0)
            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


@app.post(
    "/tailscale/{api_key}",
    summary=desc_tailscale,
    description=desc_tailscale,
    tags=["Service Webhooks"],
    status_code=status.HTTP_200_OK,
    include_in_schema=True,
)
async def webhook_tailscale(api_key: str, payload: Request):

    if api_key == app_api_key:

        try:

            result = await payload.json()

            for event in result:

                full_message = (
                    "Type: " + str(event["type"]) + "\n" + str(event["message"])
                )

                if event["data"] not in (None, ""):
                    full_message = full_message + ("\n\nData: " + str(event["data"]))

                send_output(
                    event,
                    subject_tailscale + " (" + event["tailnet"] + ")",
                    full_message,
                    "",
                    0,
                )

            return {"result": input_success}

        except Exception:

            return {"result": input_failure}

    else:

        return {"result": "Invalid API Key (" + str(status.HTTP_401_UNAUTHORIZED) + ")"}


def send_output(request_body, subject, message, url, priority):

    for output in current_outputs:

        try:

            match output:
                case "discord":
                    send_discord(subject, message, url)
                case "email":
                    send_email(subject, message, url)
                case "gotify":
                    send_gotify(subject, message, url, priority)
                case "matrix":
                    send_matrix(message)
                case "ntfysh":
                    send_ntfysh(subject, message, url, priority)
                case "pushbullet":
                    send_pushbullet(subject, message, url)
                case "pushover":
                    send_pushover(subject, message, url, priority)
                case "telegram":
                    send_telegram(subject, message, url)
                case "webhook":
                    send_webhook(request_body)

        except:

            return status.HTTP_400_BAD_REQUEST


def send_discord(subject, message, url):

    full_message = ""

    if subject and subject != "":
        full_message += subject

    if message and message != "":
        full_message += "\n" + message

    if url and url != "":
        full_message += "\n\n" + url

    headers = {
        "Content-Type": "application/json",
    }

    for account in outputs["discord"]:

        data = json.dumps({"username": account["username"], "content": full_message})

        try:

            response = requests.post(account["url"], headers=headers, data=data)
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_email(subject, message, url):

    for account in outputs["email"]:

        full_message = "From: " + account["email_sender"] + "\n"
        full_message += "To: " + account["email_receiver"] + "\n"
        full_message += "Subject: " + subject + "\n\n"
        full_message += message

        if url and url != "":
            full_message += "\n\n" + url

        if account["protocol"] == "tls":

            context = ssl.create_default_context()
            server = smtplib.SMTP(account["server"], int(account["port"]))
            server.starttls(context=context)
            server.login(account["username"], account["password"])
            server.sendmail(
                account["email_sender"], account["email_receiver"], full_message
            )


def send_gotify(subject, message, url, priority):

    full_message = ""

    if message and message != "":
        full_message = full_message + message

    if url and url != "":
        full_message = full_message + "\n\n" + url

    data = {"title": subject, "message": full_message, "priority": priority}

    for account in outputs["gotify"]:

        full_url = account["url"] + "/message?token=" + account["token"]

        try:

            response = requests.post(full_url, data=data)
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_matrix(message):

    full_message = ""

    if message and message != "":
        full_message += "\n" + message

    headers = {
        "Content-Type": "application/json",
    }

    for account in outputs["matrix"]:

        data = json.dumps({"msgtype": "m.text", "body": full_message})

        try:

            random_string = str(uuid.uuid4())

            full_url = (
                account["url"]
                + "/_matrix/client/r0/rooms/"
                + account["room"]
                + "/send/m.room.message/"
                + random_string
                + "?access_token="
                + account["token"]
            )

            response = requests.put(full_url, data=data, headers=headers)

            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_ntfysh(subject, message, url, priority):

    headers = {}

    if subject and subject != "":
        headers["Title"] = subject

    if url and url != "":
        headers["Click"] = url

    if priority and priority != "":
        headers["Priority"] = priority

    for account in outputs["ntfysh"]:

        try:

            response = requests.post(
                "https://ntfy.sh/" + account["topic"], headers=headers, data=message
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_pushbullet(subject, message, url):

    data = json.dumps(
        {
            "body": message,
            "title": subject,
            "type": "note",
            "url": url,
        }
    )

    for account in outputs["pushbullet"]:

        try:

            headers = {
                "Access-Token": account["api_key"],
                "Content-Type": "application/json",
            }

            response = requests.post(
                "https://api.pushbullet.com/v2/pushes", headers=headers, data=data
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_pushover(subject, message, url, priority):

    api_url = "https://api.pushover.net/1/messages.json"

    for account in outputs["pushover"]:

        body = {
            "message": message,
            "priority": priority,
            "title": subject,
            "token": account["api_token"],
            "url": url,
            "user": account["api_user"],
        }

        try:

            response = requests.post(url=api_url, data=body)
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_telegram(subject, message, url):

    full_message = ""

    if subject and subject != "":
        full_message = "<strong>" + subject + "</strong>"

    if message and message != "":
        full_message = full_message + "\n" + message

    if url and url != "":
        full_message = full_message + "\n\n" + url

    for account in outputs["telegram"]:

        api_url = "https://api.telegram.org/bot" + account["api_key"] + "/sendMessage"

        body = {
            "chat_id": account["user_id"],
            "disable_web_page_preview": "true",
            "parse_mode": "HTML",
            "text": full_message,
        }

        try:

            response = requests.post(url=api_url, data=body)
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)


def send_webhook(json):

    headers = {
        "Content-Type": "application/json",
    }

    for account in outputs["webhook"]:

        try:

            response = requests.post(url=account["url"], headers=headers, json=json)
            response.raise_for_status()

        except requests.exceptions.RequestException as error:

            raise SystemExit(error)
