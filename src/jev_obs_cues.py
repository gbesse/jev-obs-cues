"""OBS Python script: preview or apply one finite gateway-selected scene cue."""

import json
import os
import queue
import sys
import threading
import urllib.request
import uuid

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIRECTORY not in sys.path:
    sys.path.insert(0, SCRIPT_DIRECTORY)

import obspython as obs

from core import encoded_body, make_request, redacted_error, safe_gateway_url, validate_response

_settings = {"gateway": "http://127.0.0.1:8787/v1/decision", "signal": "", "auto_switch": False}
_revision = 0
_results = queue.Queue()
_in_flight = False


def script_description():
    return "Use a trusted Jev gateway to preview—or explicitly apply—one scene cue chosen from existing OBS scenes."


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, "gateway", "Gateway URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "signal", "Cue signal text", obs.OBS_TEXT_MULTILINE)
    obs.obs_properties_add_bool(props, "auto_switch", "Apply the selected scene (preview only when disabled)")
    obs.obs_properties_add_button(props, "run", "Evaluate cue", _run_clicked)
    return props


def script_defaults(settings):
    obs.obs_data_set_default_string(settings, "gateway", _settings["gateway"])
    obs.obs_data_set_default_bool(settings, "auto_switch", False)


def script_update(settings):
    _settings["gateway"] = obs.obs_data_get_string(settings, "gateway")
    _settings["signal"] = obs.obs_data_get_string(settings, "signal")
    _settings["auto_switch"] = obs.obs_data_get_bool(settings, "auto_switch")


def script_load(settings):
    obs.timer_add(_poll_result, 250)


def script_unload():
    obs.timer_remove(_poll_result)


def _scene_names():
    sources = obs.obs_frontend_get_scenes()
    try:
        return [obs.obs_source_get_name(source) for source in sources]
    finally:
        obs.source_list_release(sources)


def _run_clicked(props, prop):
    del props, prop
    global _revision, _in_flight
    if _in_flight:
        obs.script_log(obs.LOG_WARNING, "A Jev cue request is already running")
        return False
    token = os.environ.get("JEV_GATEWAY_TOKEN", "")
    try:
        if not token:
            raise ValueError("Set JEV_GATEWAY_TOKEN before starting OBS")
        if not safe_gateway_url(_settings["gateway"]):
            raise ValueError("Gateway requires HTTPS except on loopback")
        _revision += 1
        request = make_request(uuid.uuid4().hex, f"obs:{_revision}", _settings["signal"], _scene_names())
    except Exception as error:
        obs.script_log(obs.LOG_ERROR, redacted_error(error, token))
        return False
    _in_flight = True
    threading.Thread(
        target=_request_worker,
        args=(request, token, _settings["gateway"]),
        daemon=True,
        name="jev-obs-cue",
    ).start()
    return True


def _request_worker(request, token, gateway):
    try:
        http_request = urllib.request.Request(
            gateway, data=encoded_body(request), method="POST",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(http_request, timeout=35) as response:
            outcome = validate_response(request, json.load(response))
        _results.put((request["revision"], outcome, None))
    except Exception as error:
        _results.put((request["revision"], None, redacted_error(error, token)))


def _poll_result():
    global _in_flight
    try:
        revision, outcome, error = _results.get_nowait()
    except queue.Empty:
        return
    _in_flight = False
    if error:
        obs.script_log(obs.LOG_ERROR, f"Jev cue failed: {error}")
        return
    if revision != f"obs:{_revision}":
        obs.script_log(obs.LOG_WARNING, "Ignored stale Jev cue")
        return
    obs.script_log(obs.LOG_INFO, f"Jev cue: {outcome}" + (" (applying)" if _settings["auto_switch"] else " (preview only)"))
    if not _settings["auto_switch"]:
        return
    source = obs.obs_get_source_by_name(outcome)
    if source:
        try:
            obs.obs_frontend_set_current_scene(source)
        finally:
            obs.obs_source_release(source)
