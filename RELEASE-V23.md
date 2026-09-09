# Lumen v23 — bounded Railway deployment probes

- Fixed a TLS/proxy edge case that could leave `/health` permanently on `checking`.
- Added an independent wall-clock timeout to every HTTP CONNECT and TLS handshake.
- Added a 45-second hard deadline around the complete route-selection pass.
- A timed-out scan now becomes an explicit `failed` health state rather than hanging forever.
- Fixed selected-route latency reporting.
- The six proxy routes, direct fallback, deployment-time checks and request-scoped routing remain unchanged.
