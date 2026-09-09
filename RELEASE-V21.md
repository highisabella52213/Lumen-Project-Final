# Lumen v21 — Cloudflare proxy pool and direct fallback

- Six HTTP CONNECT proxies are embedded in the one-file installer.
- From the running Cloudflare edge, every proxy is checked against both GitHub and Railway before installation starts.
- Proxy checks run in parallel by route, while the two destination checks per route stay sequential to respect Cloudflare's six-socket concurrency limit.
- The fastest route that passes both checks is selected and remains request-scoped for every GitHub/Railway action in that installation.
- If all six proxies fail, direct Cloudflare egress is tested against both services and used only if both checks pass.
- If proxies and direct egress all fail, installation stops before any GitHub or Railway mutation.
- The HTTP response reader now completes on Content-Length or a complete chunked body instead of relying only on connection close.
- The success screen reports the selected route.
- Previous persistence safeguards, token locking, manual credential settings, translations and security controls remain active.
