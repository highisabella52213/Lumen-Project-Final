# Lumen one-file Cloudflare installer

The management panel never asks for GitHub or Railway credentials. Installation is performed by the separate `cloudflare-installer/worker.js` application.

## 1. Create the two tokens

1. GitHub classic token: <https://github.com/settings/tokens/new?scopes=public_repo&description=Lumen%20Cloudflare%20Installer>
   - Sign in to GitHub.
   - Keep the preselected `public_repo` scope.
   - Generate the token and copy it once.
2. Railway account token: <https://railway.com/account/tokens>
   - Choose **New Token** and create an account token.
   - Copy it once. Project tokens cannot create a new project.
3. In Railway, make sure GitHub is connected and can access the fork: <https://railway.com/account/integrations>

## 2. Deploy the Worker

1. Open Cloudflare Workers: <https://dash.cloudflare.com/?to=/:account/workers-and-pages/create>
2. Create a Worker, replace its starter code with the complete contents of `cloudflare-installer/worker.js`, then deploy.
3. Open the Worker URL. Enter only the GitHub and Railway tokens.
4. The installer validates both tokens, stars and forks the official source, creates the Railway project/service, provisions variables and `/data` volume, generates a public domain, and starts deployment.
5. Save the one-time generated admin password and open the returned `/dashboard` URL.

## Security

- The Worker has no KV, D1, Durable Object, analytics, or token storage.
- Tokens exist only during one HTTPS request and are sent only to GitHub and Railway.
- Responses use `Cache-Control: no-store` and a strict Content Security Policy.
- Update credentials are stored as Railway service variables so the panel can update without asking the user. The deployed application can read these credentials; use dedicated tokens and rotate/revoke them if exposure is suspected.
- Deploy the Worker in your own Cloudflare account; do not enter tokens into an installer hosted by someone else.

## Official source

<https://github.com/highisabella52213/Lumen-Project-Final>
