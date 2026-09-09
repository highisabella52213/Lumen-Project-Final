# Lumen v24 — authenticated routes and current Railway API

- Fixed the real stage-five failure by removing the unsupported service-create field used in v23.
- Uses the current Railway public API sequence: empty service, settings, variables, volume, domain, repository connection, explicit commit deployment.
- Adds `PORT=8000` and keeps the generated domain target port aligned with the application.
- Public proxy health is no longer enough: each candidate must pass authenticated GitHub `/user` and Railway `me` checks before any mutation.
- If a public-health proxy blocks authorization or account operations, the installer tries the next healthy proxy, then direct Railway egress.
- Installation errors now return bilingual step, error code and request ID instead of a generic network message.
- Railway GraphQL validation details are safely surfaced for diagnosis without returning tokens.
