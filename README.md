# Jev OBS Cues

A preview-first OBS Studio Python script that sends a bounded cue signal to your trusted gateway and accepts only one of the scenes already present in OBS. Automatic scene switching is **off by default** and must be explicitly enabled.

## Install

1. Put `src/jev_obs_cues.py` and `src/core.py` in one directory.
2. Set `JEV_GATEWAY_TOKEN` in the environment used to launch OBS.
3. Open **Tools → Scripts**, configure Python, and add `jev_obs_cues.py`.
4. Enter an HTTPS gateway URL (loopback HTTP is permitted for development), a cue signal, and click **Evaluate cue**.

Never put a TypeSafe API key in an OBS script or scene collection. The trusted gateway owns upstream credentials and registered pack `obs/scene-cue`; OBS receives a short-lived session token. Network work runs on a worker thread, late revisions are ignored, and switching remains on OBS's main timer callback.

## Try the cue contract offline

`python3 examples/offline_cue.py` now also rejects a synthetic scene that is absent from the request's allowed scene list. The script tests the contract without OBS or a network call. / Le script rejette aussi une scène absente de la liste autorisée, sans OBS ni réseau. / El script también rechaza una escena fuera de la lista permitida, sin OBS ni red.

Run `python3 examples/offline_cue.py` to build a bounded cue request, accept one synthetic gateway outcome and reject a stale revision. This exercises the engine-independent safety contract without OBS, a gateway or a TypeSafe key. It does not verify in-host scene switching.

## Test

```bash
python3 -m unittest discover -s tests -v
ruff check .
python3 -m compileall -q src
```

Tests are offline. OBS was not installed in the build environment, so loading the script and applying a real scene switch remain host-specific checks.

MIT — see [LICENSE](LICENSE).
