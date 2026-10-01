"""Explicit, backed-up correction of Nick's mislabeled imported game (September 2026).
Run only after scripts/backup.py completes; retains every score row and game ID.
"""
import json
from pathlib import Path
import sqlite3
import sys
import time


def correct(database, backup_directory):
    backup_directory = Path(backup_directory)
    if not (backup_directory / 'COMPLETE').is_file():
        raise ValueError('A complete database/photo backup is required.')
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN IMMEDIATE')
        before = dict(db.execute("SELECT * FROM games WHERE id='bubblebobble'").fetchone())
        if before['title'] == 'Bust-A-Move':
            return 'Already corrected; no changes.'
        assert before['title'] == 'Puzzle Bobble' and before['kind'] == 'points'
        assert not db.execute("SELECT 1 FROM games WHERE search_key='bustamove'").fetchone()
        scores = [dict(r) for r in db.execute('SELECT * FROM scores ORDER BY id')]
        game_count = db.execute('SELECT COUNT(*) FROM games').fetchone()[0]
        db.execute("UPDATE games SET title='Bust-A-Move',search_key='bustamove',image='images/cabinet-marquees/bust-a-move.png' WHERE id='bubblebobble'")
        after = dict(db.execute("SELECT * FROM games WHERE id='bubblebobble'").fetchone())
        score_id = db.execute("SELECT id FROM scores WHERE game_id='bubblebobble' AND user_sub='imported' ORDER BY created_at LIMIT 1").fetchone()
        if not score_id:
            score_id = db.execute("SELECT id FROM scores WHERE game_id='bubblebobble' ORDER BY created_at LIMIT 1").fetchone()
        assert score_id
        db.execute('INSERT INTO audit (score_id,actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?,?)',
                   (score_id[0], 'maintenance:ron-request-2026-09-30', 'set_bust_a_move_display', json.dumps(before), json.dumps(after), int(time.time())))
        assert scores == [dict(r) for r in db.execute('SELECT * FROM scores ORDER BY id')]
        assert db.execute('SELECT COUNT(*) FROM games').fetchone()[0] == game_count
    return 'Bust-A-Move title and artwork applied; all score rows unchanged.'


if __name__ == '__main__':
    print(correct(sys.argv[1], sys.argv[2]))
