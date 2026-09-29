# Proposed Friday deployment — prepared, not applied

The read-only VPS inspection found nginx, Python 3.12 at `/usr/local/bin/python3.12`, sufficient disk/memory, and the existing `midconversation.com` HTTPS host. No arcade service has been installed. Port 8766 availability, systemd compatibility and the exact nginx insertion still need fresh verification at deployment.

## Release layout

- GitHub Pages keeps `https://ronavis.github.io/nicks-arcade/`.
- One separate `nicks-arcade` OS account and systemd service; no Mission Control process/code/database changes.
- Immutable backend releases under `/opt/nicks-arcade/releases/<commit>/`; `current` symlink chooses release.
- Python venv under `/opt/nicks-arcade/venv`, using Python 3.12, with `server/requirements.txt` installed.
- Durable data `/var/lib/nicks-arcade`, owned by service user, directory mode 0700. Environment `/etc/nicks-arcade.env`, mode 0600.
- Bind only `127.0.0.1:8766`. Add the supplied nginx location inside the HTTPS server; it maps `/arcade-api/` to the service's `/api/`.

## Execution sequence

1. Review the exact commit and preserve the current Pages build and nginx configuration. Confirm port 8766 is unused, paths/account do not already exist, and snapshot current service health.
2. Create the isolated account/directories. Stage only `server/`, `data/`, environment example and dependencies in the release. Set `current`, install the supplied service unit and environment. Do not set `ARCADE_DEMO`.
3. Start the separate service. Verify loopback `/api/health` reports production and `/api/leaderboard` contains 32 starting games. An unsigned POST must be rejected; `/api/demo-session` must be unavailable.
4. Add only `nginx-location.conf`'s location to the existing HTTPS host. Run `nginx -t` before a reload; verify existing Mission Control endpoints still pass their established read-only health checks. If anything is ambiguous, stop and reconcile before retrying.
5. Verify the public API, exact CORS origin, no unauthenticated photo access and no public data-directory path. Avoid access-log formats containing Authorization headers.
6. In the existing Google OAuth web client, confirm authorized JavaScript origin `https://ronavis.github.io`. If the consent app is in Testing, add Friday's player accounts or move to an appropriate published consent configuration. This needs Google project-owner access; it is not proven by code tests. Do not request unnecessary Google scopes.
7. Set frontend `config.js` to `window.ARCADE_CONFIG = { apiBase: 'https://midconversation.com/arcade-api' };`, build, and publish **only `dist/`** through the chosen Pages source. Inspect the repo's current Pages settings first; do not change branch/workflow settings blindly. Never publish the backend, tests, databases or photos.
8. On a real phone, Google sign in, select Galaga, enter a disposable score and initials, attach a proof photo, submit. On the TV, verify it appears within five seconds, survives service restart, and loads without sign-in. Sign in as Ron, view photo, correct/remove the test score and verify record fallback. Verify another signed-in account cannot administer scores. Check signed-out submission is blocked.
9. Scan the production QR with a different phone. Test portrait fullscreen on Nick's actual display browser; disable device sleep. Confirm source game ambiguities and any previous real localStorage scores before declaring opening-night ready.

## Backups and recovery

Run `python scripts/backup.py /var/lib/nicks-arcade /secure/backups/arcade-YYYYMMDD-HHMM` as an account that can read the service data. Each destination must be new. The script uses SQLite's online backup API, checks integrity, copies every referenced immutable photo, and writes COMPLETE only after success. Store a private off-host copy; production scheduling/retention is an explicit deployment step, not already configured. JSON admin export is useful for inspection but does not include photos and is not a complete backup.

To restore, stop only `nicks-arcade`, preserve the current data directory, copy a COMPLETE backup into a new service-owned data directory, point the environment there and restart only this service. Verify records, photos and health before resuming submissions. Test this with a temporary data directory before relying on it.

## Rollback

Save the previous Pages artifact and nginx configuration before publication. To roll back frontend/service code, restore the previous artifact/release while preserving `/var/lib/nicks-arcade`. This release initializes a new schema; it does not migrate an existing production arcade database. Never replace live data with demo data. If removing the new API route, validate nginx before reloading; never overwrite the entire host configuration or restart unrelated services.

## Not yet verified

Google project ownership/origin/consent settings; a real Google browser login; actual phone-to-public-API traffic; live photo upload through nginx; physical QR scan; target TV model/browser/rotation behavior; production restart and scheduled/off-host backup. Local tests are evidence for implementation, not proof of these production steps.
