# Lumen v25 — direct-first control plane and token-safe validation

- Fixed v24's false `NO_AUTHENTICATED_ROUTE` failure.
- Removed Railway `me` from route qualification because that query is account-token-only and can reject otherwise reachable scoped sessions.
- Every scan now tests all six proxies and direct Railway egress.
- Token-bearing control-plane calls prefer direct Railway egress; verified proxies remain fallbacks.
- GitHub `/user` remains the only universal credential preflight before mutations.
- Railway authorization is validated by the actual project operation and GraphQL `Not Authorized` is mapped to a precise token error.
- The UI explicitly requires an Account Token created with `No workspace` selected.
