"""Synthetic, engine-independent OBS cue contract example."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core import make_request, validate_response  # noqa: E402

request = make_request("cue-1", "scene-state-7", "Speaker starts demo", ["Camera", "Slides"])
response = {
    "requestId": request["requestId"],
    "revision": request["revision"],
    "record": {
        "schemaVersion": 1,
        "pack": {"name": request["packId"]},
        "model": "synthetic-fixture",
        "outcome": "Slides",
    },
}
outcome = validate_response(request, response)
try:
    validate_response({**request, "revision": "scene-state-8"}, response)
except ValueError:
    stale_rejected = True
else:
    stale_rejected = False
assert stale_rejected
try:
    validate_response(request, {**response, "record": {**response["record"], "outcome": "Invented scene"}})
except ValueError:
    unknown_scene_rejected = True
else:
    unknown_scene_rejected = False
assert unknown_scene_rejected
print(
    json.dumps(
        {
            "source": "synthetic fixture; no OBS or network",
            "accepted_outcome": outcome,
            "stale_revision_rejected": stale_rejected,
            "unknown_scene_rejected": unknown_scene_rejected,
        },
        sort_keys=True,
    )
)
