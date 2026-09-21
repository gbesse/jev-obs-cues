"""Pure OBS cue request and provenance logic."""

import json
import re
import urllib.parse


def safe_gateway_url(url):
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"})


def make_request(request_id, revision, signal, scenes, pack_id="obs/scene-cue"):
    clean_scenes = list(dict.fromkeys(scene.strip() for scene in scenes if scene.strip()))
    if not request_id or not revision or not signal.strip():
        raise ValueError("request id, revision, and signal are required")
    if len(clean_scenes) < 2 or len(clean_scenes) > 255:
        raise ValueError("declare 2 to 255 scene outcomes")
    return {
        "requestId": request_id,
        "revision": revision,
        "packId": pack_id,
        "state": {"signal": signal.strip(), "availableScenes": clean_scenes},
        "allowedOutcomes": clean_scenes,
    }


def validate_response(request, response):
    record = response.get("record", {})
    pack = record.get("pack", {})
    if response.get("requestId") != request["requestId"] or response.get("revision") != request["revision"]:
        raise ValueError("cue request provenance mismatch")
    if record.get("schemaVersion") != 1 or pack.get("name") != request["packId"] or not record.get("model"):
        raise ValueError("invalid cue record provenance")
    if record.get("outcome") not in request["allowedOutcomes"]:
        raise ValueError("cue outcome is not an available scene")
    return record["outcome"]


def redacted_error(value, token):
    text = re.sub(r"[\r\n]+", " ", str(value))[:200]
    return text.replace(token, "[redacted]") if token else text


def encoded_body(request):
    return json.dumps(request, separators=(",", ":")).encode("utf-8")

