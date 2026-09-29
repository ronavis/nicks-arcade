# Friday deployment and recovery guide

The read-only VPS inspection found nginx, Python 3.12 at `/usr/local/bin/python3.12`, sufficient disk/memory, and the existing `midconversation.com` HTTPS host. The isolated service and API route were installed on 2026-09-29; see launch-status.md for current validation evidence. Port 8766 and the systemd units were verified during deployment.

## Release layout

- GitHub Pages keeps `https://ronavis.github.io/nicks-arcade/`.
- One separate `nicks-arcade` OS account and systemd service; no Mission Control process/code/database changes.
- Immutable backend releases under `/opt/nicks-arcade/releases/<commit>/`; `current` symlink chooses release.
- Python venv under `/opt/nicks-arcade/venv`, using Python 3.12, with `server/requirements.txt` installed.
- Durable data `/var/lib/nicks-arcade`, owned by service user, directory mode 0700. Environment `/etc/nicks-arcade.env`, mode 0600.
- Bind only `127.0.0.1:8766`. Add the supplied nginx location inside the HTTPS server; it maps `/arcade-api/` to the service's `/api/`.

## First-time installation

The live installation already exists. Do not repeat account/directory creation on the current server; use the update sequence below.

1. Review the exact commit and preserve the current Pages build and nginx configuration. Confirm port 8766 is unused, paths/account do not already exist, and snapshot current service health.
2. Create the isolated account/directories. Stage only `server/`, `data/`, environment example and dependencies in the release. Set `current`, install the supplied service unit and environment. Do not set `ARCADE_DEMO`.
3. Start the separate service. Verify loopback `/api/health` reports production and `/api/leaderboard` contains the supplied catalog (33 games at this release, including 32 starting records). An unsigned POST must be rejected; `/api/demo-session` must be unavailable.
4. Add only `nginx-location.conf`'s location to the existing HTTPS host. Run `nginx -t` before a reload; verify existing Mission Control endpoints still pass their established read-only health checks. If anything is ambiguous, stop and reconcile before retrying.
5. Verify the public API, exact CORS origin, no unauthenticated photo access and no public data-directory path. Avoid access-log formats containing Authorization headers.
6. In the existing Google OAuth web client, confirm authorized JavaScript origin `https://ronavis.github.io`. For this basic Sign in with Google flow, Google documents an exception to the Testing allowlist when only name/email/profile are requested. Do not add unrelated scopes or publish consent settings merely to work around a misunderstood Testing label. Verify actual sign-in. This needs Google project-owner access; it is not proven by code tests. Do not request unnecessary Google scopes.
7. Run `ARCADE_API_BASE=https://midconversation.com/arcade-api npm run build`, and publish **only `dist/`** through the chosen Pages source. Inspect the repo's current Pages settings first; do not change branch/workflow settings blindly. Never publish the backend, tests, databases or photos.
8. On a real phone, Google sign in, select Galaga, enter a disposable score and initials, attach a proof photo, submit. On the TV, verify it appears within five seconds, survives service restart, and loads without sign-in. Sign in as Ron, view photo, correct/remove the test score and verify record fallback. Verify another signed-in account cannot administer scores. Check signed-out submission is blocked.
9. Scan the production QR with a different phone. Test portrait fullscreen on Nick's actual display browser; disable device sleep. Confirm source game ambiguities and any previous real localStorage scores before declaring opening-night ready.

## Updating the existing installation

1. Confirm the source commit, current Pages commit, active backend release and live API health. Back up the persistent database/photos before backend changes.
2. Run the source checks and backend tests. Stage backend changes in a new immutable release, including `server/`, `data/` and `scripts/backup.py`; install its pinned dependencies in the service environment. Keep the existing data directory and environment configuration.
3. Switch the `current` symlink only after staging succeeds, then restart only `nicks-arcade`. Verify API health, existing score preservation and the behavior changed by the release. Frontend-only updates do not need a service restart.
4. The Arcade nginx route allows 41 MB of request data to accommodate a 40 MB photo plus form overhead. If changing that route, back up the current configuration, limit edits to the Arcade location, run `nginx -t` and reload only after validation.
5. Build the frontend with the production API endpoint and publish only `dist/` through a normal update to `gh-pages`. Preserve the prior commit. Wait for Pages to finish building and compare the published assets with the tested build. Version changed assets where necessary so existing browsers load the update on refresh.
6. Verify the live changed flow and record results in [launch-status.md](launch-status.md). Run a plain `npm run build` afterward if using the same checkout for local preview.

## Account and notification schema

The account release adds `profiles` (default initials and notification read cursor), `activity` (submission events) and a `taunt` column on scores. Existing scores are preserved; old submissions are not backfilled as new notifications. Activity is written in the same transaction as the score, so retrying a submission does not duplicate notifications. Full SQLite backups automatically include these tables. Prefer a forward fix or account-aware release if rollback is needed; older code will not create activity for new submissions.

## Backups and recovery

Run `python scripts/backup.py /var/lib/nicks-arcade /secure/backups/arcade-YYYYMMDD-HHMM` as an account that can read the service data. Each destination must be new. The script uses SQLite's online backup API, checks integrity, copies every referenced immutable photo, and writes COMPLETE only after success. Store a private off-host copy; the installed timer runs daily at 06:00 UTC, with missed runs caught up at boot. Backups are retained; no automatic deletion is configured. An initial private off-host copy was validated. Automatic off-host transfer is not configured. JSON admin export is useful for inspection but does not include photos and is not a complete backup.

To restore, stop only `nicks-arcade`, preserve the current data directory, copy a COMPLETE backup into a new service-owned data directory, point the environment there and restart only this service. Verify records, photos and health before resuming submissions. Test this with a temporary data directory before relying on it.

## Rollback

Save the previous Pages artifact and nginx configuration before publication. To roll back frontend/service code, restore the previous artifact/release while preserving `/var/lib/nicks-arcade`. The catalog update adds a games table without changing existing scores. Back up before deploying. Once custom games have scores, do not roll back to pre-catalog code: it cannot resolve those game IDs. Use a forward fix or a catalog-aware release while preserving live data. Never replace live data with demo data. If removing the new API route, validate nginx before reloading; never overwrite the entire host configuration or restart unrelated services.

## Remaining physical acceptance

Ron confirmed QR scanning and Google sign-in on his phone. His Bubble Bobble 254,258 / TST submission validated phone entry and was later removed at his request; the removed row remains in admin audit/history. The updated iPhone photo flow still needs his original photo retried; actual TV behavior and second-account acceptance remain pending. See launch-status.md.

## Linking imported scores to accounts

Set `ARCADE_LEGACY_OWNERS` in the private service environment to a JSON object mapping three uppercase initials to verified Google email addresses, for example `{"ABC":"player@example.com","XYZ":"player@example.com"}`. Keep real addresses out of public source and static assets. Restart the arcade service after configuration changes.

On an authenticated request, Google-authoritative Gmail or Workspace email can claim only matching unowned imported starting rows (`user_sub=imported`, `created_at=0`, `request_id=game_id`). The account email binds once to its stable Google subject in `legacy_accounts`; a different subject cannot take over that binding. Each score link increments its revision and writes a before/after audit entry. Repeated requests are idempotent. Scores submitted through the app are never matched by initials. Removed imported rows retain their removed state. Account profile initials do not affect ownership.

Existing links are durable: removing/changing the environment mapping does not transfer or unlink claimed records. Correcting an erroneous link requires a separately reviewed, backed-up administrative data correction. Full database backups include bindings and audit history. Future record-break notices work after linking; historical activity is not backfilled.

## Saved taunt settings

The taunt-settings release adds default_taunt and taunt_enabled (off by default) to profiles, plus taunt_request to scores for retry-safe submissions. Migrations preserve existing profiles and score data. Settings PATCH updates only supplied fields. Automatic taunts are resolved inside the score transaction against the current record and current profile; retries return the originally saved taunt even if settings change. Manual per-score taunts retain their existing behavior.
