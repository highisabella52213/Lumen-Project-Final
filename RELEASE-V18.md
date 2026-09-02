# Lumen v18 — one-file Cloudflare installer

- Added a standalone Material 3 Expressive Cloudflare Worker installer.
- Installer accepts only GitHub and Railway tokens.
- Automatically validates tokens, stars and forks the official source, provisions Railway, attaches `/data`, generates a domain, and deploys.
- Generates a unique admin password and application secrets.
- Removed token collection, encrypted token files, and setup write/delete APIs from the management panel.
- Updater now reads installer-provisioned Railway variables only.
- Manual proxy refresh receives a unique installer-generated enablement secret.
