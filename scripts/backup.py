"""Create a restorable database, photo and marquee snapshot, without copying active WAL files.

Usage: python scripts/backup.py /var/lib/nicks-arcade /secure/backups/arcade-YYYYMMDD
Destination must be new. Keep backups private: they include player email addresses.
"""
import argparse
import shutil
import sqlite3
import uuid
from pathlib import Path


def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not (source / 'arcade.sqlite3').is_file():
        raise ValueError('Source must contain arcade.sqlite3')
    if source == destination or source in destination.parents:
        raise ValueError('Keep backups outside the live data directory')
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    with sqlite3.connect(f'file:{source / "arcade.sqlite3"}?mode=ro', uri=True) as live:
        with sqlite3.connect(destination / 'arcade.sqlite3') as snapshot:
            live.backup(snapshot)
            if snapshot.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Database integrity check failed')
            photo_ids = snapshot.execute('SELECT DISTINCT photo_id FROM scores WHERE photo_id IS NOT NULL').fetchall()
    (destination / 'arcade.sqlite3').chmod(0o600)
    (destination / 'photos').mkdir(mode=0o700)
    # Uploaded photos are immutable and soft removal retains the original file.
    for (photo_id,) in photo_ids:
        shutil.copyfile(source / 'photos' / f'{photo_id}.jpg', destination / 'photos' / f'{photo_id}.jpg')
        (destination / 'photos' / f'{photo_id}.jpg').chmod(0o600)
    # Read image references from the consistent snapshot, including replacement history.
    with sqlite3.connect(destination / 'arcade.sqlite3') as snapshot:
        tables = {r[0] for r in snapshot.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        marquee_ids = set()
        if 'marquee_id' in {r[1] for r in snapshot.execute('PRAGMA table_info(games)')}:
            marquee_ids.update(r[0] for r in snapshot.execute('SELECT marquee_id FROM games WHERE marquee_id IS NOT NULL'))
        if 'marquee_audit' in tables:
            for previous, following in snapshot.execute('SELECT previous_id,next_id FROM marquee_audit'):
                marquee_ids.update(value for value in (previous, following) if value)
    (destination / 'marquees').mkdir(mode=0o700)
    for marquee_id in marquee_ids:
        if str(uuid.UUID(marquee_id)) != marquee_id:
            raise ValueError('Invalid stored marquee reference')
        target = destination / 'marquees' / (marquee_id + '.png')
        shutil.copyfile(source / 'marquees' / (marquee_id + '.png'), target)
        target.chmod(0o600)
    (destination / 'COMPLETE').write_text('Database integrity verified; all referenced photos and marquees copied.\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    args = parser.parse_args()
    print(backup(args.source, args.destination))
