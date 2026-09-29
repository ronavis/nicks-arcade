"""Nick's Arcade: Google-verified submissions, durable SQLite records and proof photos."""
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
import warnings
from functools import wraps
from pathlib import Path

import cachecontrol
import requests
from flask import Flask, abort, g, jsonify, request, send_from_directory
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from PIL import Image, ImageOps, UnidentifiedImageError
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parents[1]
CLIENT_ID = '569822322277-ng39tk1vcecgjfes85bs16umb5k47mc7.apps.googleusercontent.com'
Image.MAX_IMAGE_PIXELS = 24_000_000


def score_value(raw, kind):
    raw = str(raw).strip()
    if kind == 'time':
        match = re.fullmatch(r'(\d{1,2}):([0-5]\d)[.:](\d{2})', raw)
        if not match:
            raise ValueError('Enter a time as M:SS.cc, for example 1:02.30.')
        minutes, seconds, centiseconds = map(int, match.groups())
        value = (minutes * 60 + seconds) * 100 + centiseconds
    else:
        if not re.fullmatch(r'(?:\d{1,10}|\d{1,3}(?:,\d{3}){1,3})', raw):
            raise ValueError('Enter a whole-number score, up to 10 digits.')
        value = int(raw.replace(',', ''))
    if value <= 0 or value > 9_999_999_999:
        raise ValueError('The score must be greater than zero and no more than 9,999,999,999.')
    return value


def display_score(value, kind):
    if kind == 'time':
        return f'{value // 6000}:{value // 100 % 60:02d}.{value % 100:02d}'
    return f'{value:,}'


def create_app(config=None, *, allow_demo=False):
    app = Flask(__name__, static_folder=None)
    demo = os.environ.get('ARCADE_DEMO') == '1'
    app.config.update(
        DATA_DIR=os.environ.get('ARCADE_DATA_DIR'),
        GOOGLE_CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID', CLIENT_ID),
        ADMIN_EMAILS={x.strip().lower() for x in os.environ.get('ARCADE_ADMIN_EMAILS', 'ronavis@gmail.com').split(',') if x.strip()},
        ALLOWED_ORIGINS={x.strip().rstrip('/') for x in os.environ.get('ARCADE_ALLOWED_ORIGINS', 'https://ronavis.github.io').split(',') if x.strip()},
        PUBLIC_URL=os.environ.get('ARCADE_PUBLIC_URL', 'https://ronavis.github.io/nicks-arcade/'),
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
        DEMO=demo,
        TESTING=False,
    )
    if config:
        app.config.update(config)
    if app.config['DEMO'] and not allow_demo:
        raise RuntimeError('Demo mode is only available through the loopback-only local preview command.')
    if not app.config['DATA_DIR']:
        raise RuntimeError('ARCADE_DATA_DIR must point to persistent storage outside the code checkout.')
    data = Path(app.config['DATA_DIR']).resolve()
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    photos = data / 'photos'
    photos.mkdir(exist_ok=True, mode=0o700)
    database = data / 'arcade.sqlite3'
    games = json.loads((ROOT / 'data/games.json').read_text())
    by_id = {game['id']: game for game in games}
    google_request = GoogleRequest(session=cachecontrol.CacheControl(requests.Session()))
    demo_tokens = {}

    def connect():
        db = sqlite3.connect(database, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db

    with connect() as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
          CREATE TABLE IF NOT EXISTS scores (
            id TEXT PRIMARY KEY, game_id TEXT NOT NULL, value INTEGER NOT NULL CHECK(value>0),
            initials TEXT NOT NULL, user_sub TEXT NOT NULL, user_email TEXT NOT NULL,
            photo_id TEXT, created_at INTEGER NOT NULL, deleted_at INTEGER,
            revision INTEGER NOT NULL DEFAULT 1, request_id TEXT NOT NULL,
            UNIQUE(user_sub, request_id)
          );
          CREATE INDEX IF NOT EXISTS scores_game ON scores(game_id, deleted_at, value);
          CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY, score_id TEXT NOT NULL REFERENCES scores(id),
            actor TEXT NOT NULL, action TEXT NOT NULL, before_json TEXT NOT NULL,
            after_json TEXT NOT NULL, created_at INTEGER NOT NULL
          );
          CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM metadata WHERE key='seed_v1'").fetchone():
            for game in games:
                db.execute('INSERT INTO scores (id,game_id,value,initials,user_sub,user_email,created_at,request_id) VALUES (?,?,?,?,?,?,?,?)',
                           (str(uuid.uuid4()), game['id'], score_value(game['score'], game['kind']), game['initials'], 'imported', '', 0, game['id']))
            db.execute("INSERT INTO metadata VALUES ('seed_v1','1')")

    def get_db():
        if 'db' not in g:
            g.db = connect()
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        if 'db' in g:
            g.db.close()

    @app.before_request
    def origin_guard():
        if app.config['DEMO']:
            if request.remote_addr not in {'127.0.0.1', '::1'} or request.host.split(':')[0] not in {'127.0.0.1', 'localhost'}:
                abort(403, 'The preview is local only.')
        origin = request.headers.get('Origin')
        if request.path.startswith('/api/') and origin and origin not in app.config['ALLOWED_ORIGINS']:
            abort(403, 'This website is not allowed to access the arcade service.')
        if request.method == 'OPTIONS':
            return '', 204

    @app.after_request
    def headers(response):
        origin = request.headers.get('Origin')
        if origin in app.config['ALLOWED_ORIGINS']:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
            response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://accounts.google.com; style-src 'self' 'unsafe-inline' https://accounts.google.com; img-src 'self' blob: data: https://*.googleusercontent.com; font-src 'self'; connect-src 'self' https://accounts.google.com; frame-src https://accounts.google.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return error

    @app.errorhandler(ValueError)
    def invalid(error):
        return jsonify(error=str(error)), 400

    def authenticated(admin=False):
        def decorate(fn):
            @wraps(fn)
            def wrapped(*args, **kwargs):
                auth = request.headers.get('Authorization', '')
                if not auth.startswith('Bearer ') or len(auth) > 8192:
                    abort(401, 'Sign in with Google to continue.')
                token = auth[7:]
                try:
                    if app.config['DEMO'] and token in demo_tokens:
                        who = demo_tokens[token]
                        if who['exp'] <= time.time():
                            raise ValueError('Expired')
                    elif app.testing and app.config.get('TEST_TOKEN_VERIFIER'):
                        who = app.config['TEST_TOKEN_VERIFIER'](token)
                    else:
                        who = id_token.verify_oauth2_token(token, google_request, app.config['GOOGLE_CLIENT_ID'])
                    if not who.get('sub') or who.get('email_verified') is not True or not who.get('email'):
                        raise ValueError('Unverified identity')
                except (TransportError, requests.RequestException):
                    abort(503, 'Google sign-in verification is temporarily unavailable. Please try again.')
                except (ValueError, KeyError, GoogleAuthError):
                    abort(401, 'Your sign-in has expired or could not be verified. Please sign in again.')
                authoritative_email = who['email'].lower().endswith('@gmail.com') or bool(who.get('hd'))
                g.user = {'sub': who['sub'], 'email': who['email'].lower(), 'admin': authoritative_email and who['email'].lower() in app.config['ADMIN_EMAILS']}
                if admin and not g.user['admin']:
                    abort(403, 'Only the arcade administrator can change or remove scores.')
                return fn(*args, **kwargs)
            return wrapped
        return decorate

    def public_record(row):
        return {'id': row['id'], 'score': display_score(row['value'], by_id[row['game_id']]['kind']),
                'initials': row['initials'], 'createdAt': row['created_at'] or None,
                'hasPhoto': bool(row['photo_id']), 'photoId': row['photo_id'], 'revision': row['revision']}

    def winner(db, game_id):
        direction = 'ASC' if by_id[game_id]['kind'] == 'time' else 'DESC'
        return db.execute(f'SELECT * FROM scores WHERE game_id=? AND deleted_at IS NULL ORDER BY value {direction},created_at ASC,id ASC LIMIT 1', (game_id,)).fetchone()

    @app.get('/api/config')
    def configuration():
        return jsonify(googleClientId=app.config['GOOGLE_CLIENT_ID'], demo=app.config['DEMO'], publicUrl=app.config['PUBLIC_URL'])

    @app.get('/api/health')
    def health():
        get_db().execute('SELECT 1').fetchone()
        return jsonify(status='ok', version='2.0.0', mode='local-preview' if app.config['DEMO'] else 'production')

    @app.get('/api/leaderboard')
    def leaderboard():
        db = get_db()
        output = []
        for game in games:
            row = winner(db, game['id'])
            output.append({k: game[k] for k in ['id', 'title', 'image', 'kind', 'order']} | {'record': public_record(row) if row else None})
        return jsonify(games=output, updatedAt=int(time.time()))

    @app.get('/api/session')
    @authenticated()
    def session():
        return jsonify(email=g.user['email'], admin=g.user['admin'])

    if app.config['DEMO']:
        @app.post('/api/demo-session')
        def demo_session():
            # Registered only by the loopback development entry point. Never enabled by gunicorn.
            token = secrets.token_urlsafe(32)
            admin = (request.get_json(silent=True) or {}).get('role') == 'admin'
            demo_tokens[token] = {'sub': 'preview-admin' if admin else 'preview-player',
                                  'email': 'ronavis@gmail.com' if admin else 'preview-player@gmail.com',
                                  'email_verified': True, 'exp': time.time() + 3600}
            return jsonify(token=token)

    def save_photo(upload):
        if not upload or not upload.filename:
            return None
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(upload.stream) as image:
                    if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                        raise ValueError('Use a JPG, PNG or WebP photo.')
                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((1600, 1600))
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    photo_id = str(uuid.uuid4())
                    # Re-encoding strips EXIF, including location metadata, and ignores filenames.
                    image.save(photos / (photo_id + '.jpg'), format='JPEG', quality=85)
                    return photo_id
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValueError('That photo could not be read. Use a JPG, PNG or WebP under 8 MB and 24 megapixels.')

    @app.post('/api/scores')
    @authenticated()
    def submit():
        game_id = request.form.get('gameId', '')
        if game_id not in by_id:
            raise ValueError('Choose a game from the arcade collection.')
        initials = request.form.get('initials', '').strip().upper()
        if not re.fullmatch('[A-Z]{3}', initials):
            raise ValueError('Enter exactly three letters for your initials.')
        value = score_value(request.form.get('score', ''), by_id[game_id]['kind'])
        request_id = request.form.get('requestId', '')
        try:
            uuid.UUID(request_id)
        except ValueError:
            raise ValueError('The submission identifier is invalid. Reload and try again.')
        db = get_db()
        photo_id = None
        try:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT * FROM scores WHERE user_sub=? AND request_id=?', (g.user['sub'], request_id)).fetchone()
            if previous:
                if (previous['game_id'], previous['value'], previous['initials']) != (game_id, value, initials):
                    abort(409, 'This submission was already saved with different details. Start a new entry.')
                return jsonify(record=public_record(previous), duplicate=True), 200
            now = int(time.time())
            count = db.execute('SELECT COUNT(*) FROM scores WHERE user_sub=? AND created_at>?', (g.user['sub'], now - 60)).fetchone()[0]
            if count >= 5:
                abort(429, 'A few scores arrived very quickly. Wait a minute before submitting another.')
            daily = db.execute('SELECT COUNT(*) FROM scores WHERE user_sub=? AND created_at>?', (g.user['sub'], now - 86400)).fetchone()[0]
            if daily >= 100:
                abort(429, 'The daily submission limit has been reached for this account.')
            photo_id = save_photo(request.files.get('photo'))
            score_id = str(uuid.uuid4())
            db.execute('INSERT INTO scores (id,game_id,value,initials,user_sub,user_email,photo_id,created_at,request_id) VALUES (?,?,?,?,?,?,?,?,?)',
                       (score_id, game_id, value, initials, g.user['sub'], g.user['email'], photo_id, now, request_id))
            row = db.execute('SELECT * FROM scores WHERE id=?', (score_id,)).fetchone()
            best = winner(db, game_id)
            db.commit()
            return jsonify(record=public_record(row), isRecord=best['id'] == score_id), 201
        except Exception:
            db.rollback()
            if photo_id:
                (photos / (photo_id + '.jpg')).unlink(missing_ok=True)
            raise
        finally:
            if db.in_transaction:
                db.rollback()

    @app.get('/api/photos/<photo_id>')
    @authenticated()
    def photo(photo_id):
        try:
            uuid.UUID(photo_id)
        except ValueError:
            abort(404)
        row = get_db().execute('SELECT 1 FROM scores WHERE photo_id=? AND deleted_at IS NULL', (photo_id,)).fetchone()
        if not row:
            abort(404)
        return send_from_directory(photos, photo_id + '.jpg', mimetype='image/jpeg')

    @app.get('/api/admin/scores')
    @authenticated(admin=True)
    def admin_scores():
        game_id = request.args.get('gameId')
        if game_id not in by_id:
            raise ValueError('Choose a game to review its submissions.')
        rows = get_db().execute('SELECT * FROM scores WHERE game_id=? ORDER BY deleted_at IS NOT NULL, created_at DESC, id DESC LIMIT 200', (game_id,)).fetchall()
        return jsonify(scores=[public_record(row) | {'email': row['user_email'] or 'Imported starting record', 'deleted': row['deleted_at'] is not None} for row in rows])

    @app.route('/api/admin/scores/<score_id>', methods=['PATCH', 'DELETE'])
    @authenticated(admin=True)
    def modify(score_id):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ValueError('Send an object containing the correction and revision.')
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM scores WHERE id=?', (score_id,)).fetchone()
            if not row:
                abort(404)
            if payload.get('revision') != row['revision']:
                abort(409, 'This score changed in another window. Reload the list and try again.')
            if request.method == 'DELETE':
                if row['deleted_at'] is not None:
                    abort(409, 'This score has already been removed.')
                db.execute('UPDATE scores SET deleted_at=?,revision=revision+1 WHERE id=?', (int(time.time()), score_id))
                action = 'remove'
            else:
                if row['deleted_at'] is not None:
                    abort(409, 'A removed submission cannot be edited.')
                value = score_value(payload.get('score', ''), by_id[row['game_id']]['kind'])
                initials = str(payload.get('initials', '')).upper().strip()
                if not re.fullmatch('[A-Z]{3}', initials):
                    raise ValueError('Enter exactly three letters.')
                db.execute('UPDATE scores SET value=?,initials=?,revision=revision+1 WHERE id=?', (value, initials, score_id))
                action = 'correct'
            after = db.execute('SELECT * FROM scores WHERE id=?', (score_id,)).fetchone()
            db.execute('INSERT INTO audit (score_id,actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?,?)',
                       (score_id, g.user['sub'], action, json.dumps(dict(row)), json.dumps(dict(after)), int(time.time())))
        return jsonify(ok=True)

    @app.get('/api/admin/export')
    @authenticated(admin=True)
    def export():
        response = jsonify(games=games, scores=[dict(row) for row in get_db().execute('SELECT * FROM scores')], audit=[dict(row) for row in get_db().execute('SELECT * FROM audit')])
        response.headers['Content-Disposition'] = 'attachment; filename="nicks-arcade-records.json"'
        return response

    @app.get('/')
    def index():
        return send_from_directory(ROOT / 'dist', 'index.html')

    @app.get('/<path:path>')
    def assets(path):
        if path.startswith('api/'):
            abort(404)
        return send_from_directory(ROOT / 'dist', path)

    return app


if __name__ == '__main__':
    demo = os.environ.get('ARCADE_DEMO') == '1'
    port = int(os.environ.get('PORT', '4173'))
    if demo:
        os.environ.setdefault('ARCADE_DATA_DIR', str(ROOT / '.local-preview'))
        os.environ.setdefault('ARCADE_ALLOWED_ORIGINS', f'http://127.0.0.1:{port},http://localhost:{port}')
        os.environ.setdefault('ARCADE_PUBLIC_URL', f'http://127.0.0.1:{port}/')
    create_app(allow_demo=True).run(host='127.0.0.1', port=port, debug=False)
