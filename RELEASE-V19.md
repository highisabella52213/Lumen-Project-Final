# Lumen v19 — durable updates and installer redesign

- Atomic state writes with fsync and two rolling backups.
- Mandatory state flush and signed compressed Railway snapshot before update deployment.
- Startup recovery order: primary file, rolling backups, Railway snapshot.
- Refuses to overwrite existing corrupt state with an empty database.
- Installer requires and verifies persistent `/data` storage.
- Vazirmatn loaded from Google Fonts and applied to the full installer.
- Installer composition changed to a restrained, practical setup layout.
