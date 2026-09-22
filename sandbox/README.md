# Stellawish Offline Sandbox

The sandbox does not start NoneBot, read online QQ configuration, or contact real score APIs. Every score request is intercepted by `httpx.MockTransport`; unexpected requests fail immediately.

Run from the repository root:

```text
python -m sandbox
```

The checks load the checked-in API samples and exercise:

- song and chart ID resolution;
- both providers' single-score and B50 loaders;
- B50 image rendering;
- song information image rendering;
- MInfo Markdown output.

The checked-in fixtures are `sy_b50.json`, `b50_lx.json`, `single_643_sy.json`, and `single_643_lx.json`. Their score records are used directly as mocked API response data; only minimal chart metadata unavailable in these responses is derived for rendering.

Generated images are written under `sandbox/output/` and are ignored by git.

For machine-readable output:

```text
python -m sandbox --json
```

