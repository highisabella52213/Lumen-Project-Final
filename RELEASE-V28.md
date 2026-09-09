# Lumen v28 — verified deployment completion

- Enables outbound IPv6 before deployment with `ipv6EgressEnabled: true`.
- Pins the service to US East Metal, Virginia (`us-east4-eqdc4a`) with a one-replica multi-region configuration.
- Polls the Railway deployment every 20 seconds, at most seven times.
- Returns success only after Railway reports `SUCCESS`; terminal failures and seven-check timeouts are explicit.
- Continues polling after an empty response or transient status-query error instead of returning early.
- Uses an asynchronous installation job and a status endpoint so Railway/proxy HTTP timeouts cannot turn a running deployment into an invalid installer response.
- Displays the current phase, Railway deployment status, and check count live in Persian and English.
