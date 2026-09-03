# Lumen v20 — enforced installer proxy and protected manual credentials

- Every Cloudflare installer request to GitHub and Railway uses the fixed HTTP proxy `176.111.37.216:39811` with HTTP CONNECT and end-to-end TLS certificate verification.
- No direct network fallback exists in the installer; a failed proxy produces a specific bilingual error instead of bypassing the requested route.
- The installer is explicitly public and reusable: every user deploys the same single `worker.js` file in their own Cloudflare account.
- Installer-created Railway services mark credentials as installer-managed and locked.
- Manual Railway deployments can enter GitHub/Railway tokens from Lumen Settings. Lumen verifies them and stores them as protected Railway service variables.
- Replacing stored tokens requires an explicit warning confirmation. Tokens are never returned to the browser or written to logs.
- Persian translations were expanded for settings, dialogs, toasts, errors, and dynamic panel content.
- v19 atomic state, rolling backups, signed Railway snapshot, and mandatory Volume safeguards remain active.

> Cloudflare Workers must use compatibility date `2026-08-04` or later so the one-file Worker can use `node:net` and `node:tls`.
