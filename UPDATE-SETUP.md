# Lumen public one-file Cloudflare installer — v20

The installer is a public, reusable one-file application. Every user should deploy `cloudflare-installer/worker.js` in their **own** Cloudflare account and must never submit tokens to a Worker controlled by another person.

## 1. Create the two tokens

1. GitHub classic token: <https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Cloudflare%20Installer>
   - Keep the preselected `public_repo` scope.
2. Railway account token: <https://railway.com/account/tokens>
   - Use an Account Token; a Project Token cannot create a project.
3. Connect GitHub to Railway and allow access to the fork: <https://railway.com/account/integrations>

## 2. Deploy the Worker

1. Open Cloudflare Workers: <https://dash.cloudflare.com/?to=/:account/workers-and-pages/create>
2. Create a Worker with compatibility date **2026-08-04 or later**.
3. Replace the starter code with the complete contents of `cloudflare-installer/worker.js` and deploy.
4. Open the Worker URL, enter the two tokens, and start setup.
5. Save the generated admin password and open the returned `/dashboard` URL.

The Worker stars and forks the fixed official source, creates the Railway project/service, protected variables, mandatory `/data` Volume and public domain, then starts deployment.

## Enforced HTTP proxy

All server-side requests from the Cloudflare installer to GitHub and Railway are forced through:

```text
176.111.37.216:39811
```

The Worker creates an HTTP CONNECT tunnel and then performs TLS with the destination hostname and certificate validation. GitHub/Railway tokens remain inside end-to-end TLS. There is intentionally **no direct fallback**; if the proxy is unavailable, installation stops with a clear bilingual error.

## Manual deployments

If someone deploys the repository manually on Railway, open **Lumen → Settings → Update credentials** and enter:

- the deployed repository (`owner/repository`),
- branch,
- Railway Account Token,
- GitHub token.

Lumen verifies the repository/token relationship and saves the values as protected Railway service variables. Installer-created values appear filled by status, stay locked, and are never exposed. Changing any protected value requires acknowledging a warning first; blank token fields keep existing secrets.

## Security

- The Worker has no KV, D1, Durable Object, Cache API, analytics, or token persistence.
- Tokens are copied only into each user's own protected Railway service variables.
- Responses use `Cache-Control: no-store` and a strict Content Security Policy.
- The fixed proxy can observe destination names and connection metadata, but CONNECT keeps API payloads and tokens inside verified TLS.
- Rotate/revoke both tokens immediately if they are entered into an untrusted Worker.

Official source: <https://github.com/highisabella52213/Lumen-Project-Final>
