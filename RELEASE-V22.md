# Lumen v22 — Railway-hosted adaptive installer

- Cloudflare installer was removed.
- The complete installer now lives in `railway-installer/` and deploys as a standalone Node.js 22 Railway service.
- The six supplied HTTP proxies remain embedded.
- Railway deployment readiness tests every proxy against both GitHub and Railway.
- The fastest route passing both checks is selected; direct Railway egress is tried only after all proxies fail.
- `/health` stays unavailable until a complete route works, preventing a false-success deployment.
- Network checks repeat every five minutes and before every installation.
- The selected route remains request-scoped through every GitHub and Railway operation.
- HTTP CONNECT uses verified end-to-end TLS, SNI and certificate validation.
- Existing persistent state, credential locking, WS-only transport, updater and dashboard safeguards remain active.
