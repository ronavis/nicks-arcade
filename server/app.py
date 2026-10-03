"""Nick's Arcade: Google-verified submissions, durable SQLite records and proof photos."""
import hashlib
import unicodedata
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
from pillow_heif import register_heif_opener
from werkzeug.exceptions import HTTPException
from server import cabinets, inventory_import

ROOT = Path(__file__).resolve().parents[1]
CLIENT_ID = '569822322277-ng39tk1vcecgjfes85bs16umb5k47mc7.apps.googleusercontent.com'
Image.MAX_IMAGE_PIXELS = 64_000_000
register_heif_opener(thumbnails=False, decode_threads=2)


def clean_taunt(value):
    value = ' '.join(str(value).split())
    if len(value) > 140 or any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('Keep your taunt to 140 characters of friendly arcade rivalry.')
    return value


def game_key(title):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', title).lower())


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
        MAX_CONTENT_LENGTH=41 * 1024 * 1024,
        LEGACY_OWNERS=json.loads(os.environ.get('ARCADE_LEGACY_OWNERS', '{}')),
        DEMO=demo,
        TESTING=False,
    )
    if config:
        app.config.update(config)
    legacy_owners = app.config['LEGACY_OWNERS']
    if not isinstance(legacy_owners, dict) or any(
            not re.fullmatch('[A-Z]{3}', initials) or not isinstance(email, str)
            or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email)
            for initials, email in legacy_owners.items()):
        raise RuntimeError('ARCADE_LEGACY_OWNERS must map three uppercase initials to account emails.')
    legacy_owners = {initials: email.lower() for initials, email in legacy_owners.items()}
    if app.config['DEMO'] and not allow_demo:
        raise RuntimeError('Demo mode is only available through the loopback-only local preview command.')
    if not app.config['DATA_DIR']:
        raise RuntimeError('ARCADE_DATA_DIR must point to persistent storage outside the code checkout.')
    data = Path(app.config['DATA_DIR']).resolve()
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    photos = data / 'photos'
    photos.mkdir(exist_ok=True, mode=0o700)
    marquees = data / 'marquees'
    marquees.mkdir(exist_ok=True, mode=0o700)
    database = data / 'arcade.sqlite3'
    games = json.loads((ROOT / 'data/games.json').read_text())
    artwork_catalog = {entry['id']: entry for entry in json.loads((ROOT / 'data/arcade-catalog.json').read_text())}
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
          CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, search_key TEXT NOT NULL UNIQUE,
            image TEXT NOT NULL, kind TEXT NOT NULL, sort_order INTEGER NOT NULL
          );
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
          CREATE TABLE IF NOT EXISTS legacy_accounts (email TEXT PRIMARY KEY, user_sub TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS profiles (user_sub TEXT PRIMARY KEY, initials TEXT NOT NULL DEFAULT '', read_event INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY AUTOINCREMENT, score_id TEXT NOT NULL UNIQUE REFERENCES scores(id), previous_sub TEXT, previous_initials TEXT, previous_value INTEGER, is_record INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS marquee_audit (id INTEGER PRIMARY KEY, game_id TEXT NOT NULL, actor TEXT NOT NULL, previous_id TEXT, next_id TEXT, created_at INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS arcade_sessions (token_hash TEXT PRIMARY KEY, identity_json TEXT NOT NULL, expires_at INTEGER NOT NULL);
          CREATE INDEX IF NOT EXISTS arcade_sessions_expiry ON arcade_sessions(expires_at);
        ''')
        if 'taunt' not in {row[1] for row in db.execute('PRAGMA table_info(scores)')}:
            db.execute("ALTER TABLE scores ADD COLUMN taunt TEXT NOT NULL DEFAULT ''")
        for name, definition in [('default_taunt', "TEXT NOT NULL DEFAULT ''"), ('taunt_enabled', 'INTEGER NOT NULL DEFAULT 0')]:
            if name not in {row[1] for row in db.execute('PRAGMA table_info(profiles)')}:
                db.execute(f'ALTER TABLE profiles ADD COLUMN {name} {definition}')
        if 'taunt_request' not in {row[1] for row in db.execute('PRAGMA table_info(scores)')}:
            db.execute('ALTER TABLE scores ADD COLUMN taunt_request TEXT')
        if 'eligible' not in {row[1] for row in db.execute('PRAGMA table_info(games)')}:
            db.execute('ALTER TABLE games ADD COLUMN eligible INTEGER NOT NULL DEFAULT 1')
        if 'marquee_id' not in {row[1] for row in db.execute('PRAGMA table_info(games)')}:
            db.execute('ALTER TABLE games ADD COLUMN marquee_id TEXT')
        db.execute("BEGIN IMMEDIATE")
        for game in games:
            db.execute('INSERT OR IGNORE INTO games (id,title,search_key,image,kind,sort_order) VALUES (?,?,?,?,?,?)',
                       (game['id'], game['title'], game_key(game['title']), game['image'], game['kind'], game['order']))
        if not db.execute("SELECT 1 FROM metadata WHERE key='seed_v1'").fetchone():
            for game in games:
                if not game.get('score'):
                    continue
                db.execute('INSERT INTO scores (id,game_id,value,initials,user_sub,user_email,created_at,request_id) VALUES (?,?,?,?,?,?,?,?)',
                           (str(uuid.uuid4()), game['id'], score_value(game['score'], game['kind']), game['initials'], 'imported', '', 0, game['id']))
            db.execute("INSERT INTO metadata VALUES ('seed_v1','1')")

    with connect() as db:
        cabinets.initialize(db, ROOT / "data/cabinets.json", game_key)
        if 'show_on_leaderboard' not in {row[1] for row in db.execute('PRAGMA table_info(games)')}:
            db.execute('ALTER TABLE games ADD COLUMN show_on_leaderboard INTEGER NOT NULL DEFAULT 0')
            db.execute('UPDATE games SET show_on_leaderboard=1 WHERE EXISTS (SELECT 1 FROM scores WHERE scores.game_id=games.id AND deleted_at IS NULL)')


    def get_db():
        if 'db' not in g:
            g.db = connect()
        return g.db

    def catalog():
        if 'catalog' not in g:
            g.catalog = {row['id']: dict(row) for row in get_db().execute('SELECT id,title,image,kind,eligible,show_on_leaderboard AS showOnLeaderboard,marquee_id AS marqueeId,sort_order AS \"order\" FROM games ORDER BY sort_order,title')}
        return g.catalog

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
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        if request.path.startswith('/api/'):
            public_art = request.path.startswith(('/api/marquees/', '/api/cabinet-photos/'))
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable' if public_art and response.status_code in (200, 304) else 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://accounts.google.com; style-src 'self' 'unsafe-inline' https://accounts.google.com; img-src 'self' blob: data: https://*.googleusercontent.com https://raw.githubusercontent.com; font-src 'self'; connect-src 'self' https://accounts.google.com; frame-src https://accounts.google.com; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
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
                    if token.startswith('arcade_'):
                        # Arcade device sessions do not grant access to other hosted apps.
                        if request.path.startswith('/api/movie-ladder/'):
                            abort(401, 'Sign in to Movie Ladder separately.')
                        saved = get_db().execute('SELECT identity_json,expires_at FROM arcade_sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
                        if not saved or saved['expires_at'] <= time.time():
                            raise ValueError('Expired session')
                        who = json.loads(saved['identity_json'])
                    elif app.config['DEMO'] and token in demo_tokens:
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
                g.verified_identity = who
                authoritative_email = who['email'].lower().endswith('@gmail.com') or bool(who.get('hd'))
                g.user = {'sub': who['sub'], 'email': who['email'].lower(), 'admin': authoritative_email and who['email'].lower() in app.config['ADMIN_EMAILS']}
                if admin and not g.user['admin']:
                    abort(403, 'Only the arcade administrator can change or remove scores.')
                if authoritative_email:
                    link_legacy_records(g.user)
                return fn(*args, **kwargs)
            return wrapped
        return decorate

    def link_legacy_records(user):
        # Only the private server configuration grants legacy ownership. Submitted
        # initials and profile preferences never grant ownership of another score.
        aliases = [initials for initials, email in legacy_owners.items() if email == user['email']]
        if not aliases:
            return
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO legacy_accounts(email,user_sub) VALUES (?,?)',
                       (user['email'], user['sub']))
            bound = db.execute('SELECT user_sub FROM legacy_accounts WHERE email=?', (user['email'],)).fetchone()
            if bound['user_sub'] != user['sub']:
                return  # An email alone cannot move records from an already bound Google identity.
            placeholders = ','.join('?' for _ in aliases)
            rows = db.execute(f"SELECT * FROM scores WHERE user_sub='imported' AND created_at=0 AND request_id=game_id AND initials IN ({placeholders})", aliases).fetchall()
            for row in rows:
                db.execute('UPDATE scores SET user_sub=?,user_email=?,revision=revision+1 WHERE id=?',
                           (user['sub'], user['email'], row['id']))
                after = db.execute('SELECT * FROM scores WHERE id=?', (row['id'],)).fetchone()
                db.execute('INSERT INTO audit(score_id,actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?,?)',
                           (row['id'], user['sub'], 'link_legacy_account', json.dumps(dict(row)), json.dumps(dict(after)), int(time.time())))

    def public_record(row):
        return {'id': row['id'], 'score': display_score(row['value'], catalog()[row['game_id']]['kind']),
                'initials': row['initials'], 'createdAt': row['created_at'] or None,
                'taunt': row['taunt'], 'hasPhoto': bool(row['photo_id']), 'photoId': row['photo_id'], 'revision': row['revision']}

    def winner(db, game_id):
        direction = 'ASC' if catalog()[game_id]['kind'] == 'time' else 'DESC'
        return db.execute(f'SELECT * FROM scores WHERE game_id=? AND deleted_at IS NULL ORDER BY value {direction},created_at ASC,rowid ASC LIMIT 1', (game_id,)).fetchone()

    def display_settings():
        row = get_db().execute("SELECT value FROM metadata WHERE key='rotation_seconds'").fetchone()
        bypass = get_db().execute("SELECT value FROM metadata WHERE key='bypass_games_restriction'").fetchone()
        return {'rotationSeconds': int(row['value']) if row else 15, 'bypassGamesRestriction': bool(bypass and bypass['value'] == '1')}

    @app.patch('/api/admin/display-settings')
    @authenticated(admin=True)
    def save_display_settings():
        payload = request.get_json(silent=True)
        seconds = payload.get('rotationSeconds', display_settings()['rotationSeconds']) if isinstance(payload, dict) else None
        if isinstance(payload, dict) and 'bypassGamesRestriction' in payload and type(payload['bypassGamesRestriction']) is not bool:
            raise ValueError('Choose on or off for the game restriction bypass.')
        if type(seconds) is not int or not 5 <= seconds <= 120:
            raise ValueError('Choose a whole number from 5 to 120 seconds.')
        with get_db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO metadata(key,value) VALUES ('rotation_seconds',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(seconds),))
            if 'bypassGamesRestriction' in payload:
                db.execute("INSERT INTO metadata(key,value) VALUES ('bypass_games_restriction',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", ('1' if payload['bypassGamesRestriction'] else '0',))
        return jsonify(displaySettings=display_settings())

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
        for game in catalog().values():
            row = winner(db, game['id'])
            record = public_record(row) if row else None
            if record:
                record['improvement'] = None
                event = db.execute('SELECT previous_value FROM activity WHERE score_id=? AND is_record=1 ORDER BY id DESC LIMIT 1', (row['id'],)).fetchone()
                # Corrections may change the original comparison; omit uncertain margins.
                if row['revision'] == 1 and event and event['previous_value'] is not None:
                    delta = event['previous_value'] - row['value'] if game['kind'] == 'time' else row['value'] - event['previous_value']
                    if delta > 0:
                        amount = f'{delta / 100:.2f}s' if game['kind'] == 'time' else f'{delta:,}'
                        record['improvement'] = {'amount': amount, 'direction': 'down' if game['kind'] == 'time' else 'up', 'label': f'Beat previous record by {amount}' + (' (faster)' if game['kind'] == 'time' else ' points')}
            assigned = [dict(c) for c in db.execute('SELECT c.id,c.name,c.code,c.photo_id AS photoId FROM cabinets c JOIN cabinet_games cg ON cg.cabinet_id=c.id WHERE cg.game_id=? ORDER BY c.name COLLATE NOCASE', (game['id'],))]
            output.append({k: game[k] for k in ['id', 'title', 'image', 'kind', 'order', 'eligible', 'marqueeId', 'showOnLeaderboard']} | {'record': record, 'cabinets': assigned})
        return jsonify(games=output, updatedAt=int(time.time()), displaySettings=display_settings())

    @app.post('/api/session')
    @authenticated()
    def create_device_session():
        if request.headers.get('Authorization', '').startswith('Bearer arcade_'):
            abort(400, 'Sign in with Google to start a new session.')
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or type(payload.get('remember')) is not bool:
            raise ValueError('Choose whether to remember this device.')
        token = 'arcade_' + secrets.token_urlsafe(32)
        expires = int(time.time()) + (30 * 86400 if payload['remember'] else 86400)
        identity = {key: g.verified_identity[key] for key in ('sub', 'email', 'email_verified', 'hd') if key in g.verified_identity}
        with get_db() as db:
            db.execute('DELETE FROM arcade_sessions WHERE expires_at<=?', (int(time.time()),))
            db.execute('INSERT INTO arcade_sessions VALUES (?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), json.dumps(identity), expires))
        return jsonify(token=token, expiresAt=expires, user=g.user)

    @app.delete('/api/session')
    @authenticated()
    def revoke_device_session():
        token = request.headers['Authorization'][7:]
        with get_db() as db:
            db.execute('DELETE FROM arcade_sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
        return jsonify(ok=True)

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
        upload.stream.seek(0, 2)
        if upload.stream.tell() > 40 * 1024 * 1024:
            raise ValueError('Choose a photo under 40 MB. Most camera photos work as they are.')
        upload.stream.seek(0)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(upload.stream) as image:
                    if image.format not in {'JPEG', 'PNG', 'WEBP', 'HEIF'}:
                        raise ValueError('Choose an iPhone HEIC, JPG, PNG or WebP photo.')
                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((1600, 1600))
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    photo_id = str(uuid.uuid4())
                    # Re-encoding strips EXIF, including location metadata, and ignores filenames.
                    image.save(photos / (photo_id + '.jpg'), format='JPEG', quality=85)
                    return photo_id
        except (Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise ValueError('That photo exceeds 64 megapixels. Choose a regular camera photo instead of a panorama.')
        except (UnidentifiedImageError, OSError, SyntaxError):
            raise ValueError('That photo could not be opened. Try selecting it again. iPhone HEIC, JPG, PNG and WebP photos are supported.')

    @app.post('/api/scores')
    @authenticated()
    def submit():
        game_id = request.form.get('gameId', '')
        picked = artwork_catalog.get(request.form.get('catalogId', ''))
        if request.form.get('catalogId') and not picked:
            raise ValueError('Choose a valid game from the marquee catalog.')
        new_title = picked['title'] if picked else ' '.join(request.form.get('gameTitle', '').split())
        kind = picked['kind'] if picked else request.form.get('gameKind', 'points')
        new_key = game_key(new_title)
        if new_title:
            if not 2 <= len(new_title) <= (250 if picked else 80) or not new_key or any(unicodedata.category(c).startswith('C') for c in new_title):
                raise ValueError('Enter a game name between 2 and 80 characters.')
            if kind not in {'points', 'time'}:
                raise ValueError('Choose points or fastest time for the new game.')
            existing = get_db().execute('SELECT id,kind FROM games WHERE search_key=?', (new_key,)).fetchone()
            game_id = existing['id'] if existing else 'custom-' + hashlib.sha256(new_key.encode()).hexdigest()[:24]
            if existing and existing['kind'] != kind:
                raise ValueError('That game already exists with a different score type. Choose it from search.')
        elif game_id not in catalog():
            raise ValueError('Choose a game from the arcade collection.')
        else:
            kind = catalog()[game_id]['kind']
        initials = request.form.get('initials', '').strip().upper()
        if not re.fullmatch('[A-Z]{3}', initials):
            raise ValueError('Enter exactly three letters for your initials.')
        value = score_value(request.form.get('score', ''), kind)
        taunt = clean_taunt(request.form.get('taunt', ''))
        automatic_taunt = request.form.get('automaticTaunt') == 'true'
        taunt_request = json.dumps([taunt, automatic_taunt])
        request_id = request.form.get('requestId', '')
        try:
            uuid.UUID(request_id)
        except ValueError:
            raise ValueError('The submission identifier is invalid. Reload and try again.')
        db = get_db()
        photo_id = None
        try:
            db.execute('BEGIN IMMEDIATE')
            approved = db.execute('SELECT eligible FROM games WHERE id=?', (game_id,)).fetchone()
            if not display_settings()['bypassGamesRestriction'] and (not approved or not approved['eligible']):
                abort(403, description="This game is not in Nick’s arcade. Ask an admin to add it first.")
            if new_title:
                db.execute('INSERT OR IGNORE INTO games (id,title,search_key,image,kind,sort_order) VALUES (?,?,?,?,?,?)',
                           (game_id, new_title, new_key, 'images/new-game.svg', kind, 1000))
                if not approved:
                    db.execute('UPDATE games SET eligible=0,image=? WHERE id=?', (picked['image'] if picked else 'images/new-game.svg', game_id))
                g.pop('catalog', None)
                existing = db.execute('SELECT id,kind FROM games WHERE search_key=?', (new_key,)).fetchone()
                game_id = existing['id']
                if existing['kind'] != kind:
                    raise ValueError('That game already exists with a different score type. Choose it from search.')
            previous = db.execute('SELECT * FROM scores WHERE user_sub=? AND request_id=?', (g.user['sub'], request_id)).fetchone()
            if previous:
                if (previous['game_id'], previous['value'], previous['initials'], previous['taunt_request'] or json.dumps([previous['taunt'], False])) != (game_id, value, initials, taunt_request):
                    abort(409, 'This submission was already saved with different details. Start a new entry.')
                return jsonify(record=public_record(previous), game=catalog()[game_id], isRecord=winner(db, game_id)['id'] == previous['id'], duplicate=True), 200
            now = int(time.time())
            count = db.execute('SELECT COUNT(*) FROM scores WHERE user_sub=? AND created_at>?', (g.user['sub'], now - 60)).fetchone()[0]
            if count >= 5:
                abort(429, 'A few scores arrived very quickly. Wait a minute before submitting another.')
            daily = db.execute('SELECT COUNT(*) FROM scores WHERE user_sub=? AND created_at>?', (g.user['sub'], now - 86400)).fetchone()[0]
            if daily >= 100:
                abort(429, 'The daily submission limit has been reached for this account.')
            previous_winner = winner(db, game_id)
            if automatic_taunt:
                profile = db.execute('SELECT default_taunt,taunt_enabled FROM profiles WHERE user_sub=?', (g.user['sub'],)).fetchone()
                beats = previous_winner and (value < previous_winner['value'] if kind == 'time' else value > previous_winner['value'])
                taunt = profile['default_taunt'] if profile and profile['taunt_enabled'] and beats and previous_winner['user_sub'] != g.user['sub'] else ''
            photo_id = save_photo(request.files.get('photo'))
            score_id = str(uuid.uuid4())
            db.execute('INSERT INTO scores (id,game_id,value,initials,user_sub,user_email,photo_id,created_at,request_id) VALUES (?,?,?,?,?,?,?,?,?)',
                       (score_id, game_id, value, initials, g.user['sub'], g.user['email'], photo_id, now, request_id))
            db.execute('UPDATE scores SET taunt=?,taunt_request=? WHERE id=?', (taunt, taunt_request, score_id))
            row = db.execute('SELECT * FROM scores WHERE id=?', (score_id,)).fetchone()
            best = winner(db, game_id)
            db.execute('INSERT INTO activity (score_id,previous_sub,previous_initials,previous_value,is_record) VALUES (?,?,?,?,?)', (score_id, previous_winner['user_sub'] if previous_winner else None, previous_winner['initials'] if previous_winner else None, previous_winner['value'] if previous_winner else None, int(best['id'] == score_id)))
            db.commit()
            return jsonify(record=public_record(row), game=catalog()[game_id], isRecord=best['id'] == score_id), 201
        except Exception:
            db.rollback()
            if photo_id:
                (photos / (photo_id + '.jpg')).unlink(missing_ok=True)
            raise
        finally:
            if db.in_transaction:
                db.rollback()

    @app.get('/api/account')
    @authenticated()
    def account():
        db = get_db()
        profile = db.execute('SELECT * FROM profiles WHERE user_sub=?', (g.user['sub'],)).fetchone()
        cursor = profile['read_event'] if profile else 0
        unread = db.execute('SELECT COUNT(*) FROM activity a JOIN scores s ON s.id=a.score_id WHERE a.id>? AND s.user_sub!=? AND s.deleted_at IS NULL', (cursor, g.user['sub'])).fetchone()[0]
        rows = db.execute('SELECT * FROM scores WHERE user_sub=? ORDER BY created_at DESC,rowid DESC LIMIT 100', (g.user['sub'],)).fetchall()
        return jsonify(defaultTaunt=profile['default_taunt'] if profile else '', tauntEnabled=bool(profile['taunt_enabled']) if profile else False, displaySettings=display_settings(), initials=profile['initials'] if profile else '', unread=unread, scores=[public_record(row) | {'gameTitle': catalog()[row['game_id']]['title'], 'deleted': row['deleted_at'] is not None, 'isRecord': row['deleted_at'] is None and winner(db,row['game_id'])['id']==row['id']} for row in rows])

    @app.patch('/api/account')
    @authenticated()
    def save_account():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ValueError('Send an object containing your settings.')
        updates = {}
        if 'initials' in payload:
            initials = str(payload['initials']).strip().upper()
            if initials and not re.fullmatch('[A-Z]{3}', initials):
                raise ValueError('Enter three letters or leave default initials blank.')
            updates['initials'] = initials
        if 'defaultTaunt' in payload:
            updates['default_taunt'] = clean_taunt(payload['defaultTaunt'])
        if 'tauntEnabled' in payload:
            if type(payload['tauntEnabled']) is not bool:
                raise ValueError('Choose whether your automatic taunt is enabled.')
            updates['taunt_enabled'] = int(payload['tauntEnabled'])
        with get_db() as db:
            db.execute('INSERT OR IGNORE INTO profiles(user_sub) VALUES (?)', (g.user['sub'],))
            for column, value in updates.items():
                db.execute(f'UPDATE profiles SET {column}=? WHERE user_sub=?', (value,g.user['sub']))
        return jsonify(ok=True)

    @app.get('/api/activity')
    @authenticated()
    def activity():
        db = get_db()
        profile = db.execute('SELECT read_event FROM profiles WHERE user_sub=?', (g.user['sub'],)).fetchone()
        cursor = profile['read_event'] if profile else 0
        rows = db.execute('SELECT a.*,s.game_id,s.value,s.initials,s.taunt,s.user_sub,s.created_at,s.revision FROM activity a JOIN scores s ON s.id=a.score_id WHERE s.deleted_at IS NULL ORDER BY a.id DESC LIMIT 100').fetchall()
        events = []
        for row in rows:
            game = catalog()[row['game_id']]
            events.append(dict(id=row['id'], gameTitle=game['title'], score=display_score(row['value'],game['kind']), initials=row['initials'], taunt=row['taunt'], createdAt=row['created_at'], isRecord=bool(row['is_record']), yourRecordBroken=bool(row['is_record'] and row['previous_sub']==g.user['sub'] and row['user_sub']!=g.user['sub']), previousInitials=row['previous_initials'], previousScore=display_score(row['previous_value'],game['kind']) if row['previous_value'] else None, unread=row['id']>cursor and row['user_sub']!=g.user['sub'], corrected=row['revision']>1))
        return jsonify(events=events, latestId=events[0]['id'] if events else 0)

    @app.post('/api/activity/read')
    @authenticated()
    def mark_activity_read():
        value = (request.get_json(silent=True) or {}).get('throughId')
        if type(value) is not int or value < 0:
            raise ValueError('Choose a valid notification to mark as read.')
        with get_db() as db:
            latest = db.execute('SELECT COALESCE(MAX(id),0) FROM activity').fetchone()[0]
            value = min(value,latest)
            db.execute('INSERT INTO profiles(user_sub,read_event) VALUES (?,?) ON CONFLICT(user_sub) DO UPDATE SET read_event=MAX(profiles.read_event,excluded.read_event)', (g.user['sub'],value))
        return jsonify(ok=True)

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

    @app.get('/api/marquees/<marquee_id>')
    def public_marquee(marquee_id):
        try:
            if str(uuid.UUID(marquee_id)) != marquee_id:
                abort(404)
        except ValueError:
            abort(404)
        if not get_db().execute('SELECT 1 FROM games WHERE marquee_id=?', (marquee_id,)).fetchone():
            abort(404)
        return send_from_directory(marquees, marquee_id + '.png', mimetype='image/png')

    @app.route('/api/admin/games/<game_id>/marquee', methods=['POST', 'DELETE'])
    @authenticated(admin=True)
    def set_marquee(game_id):
        if game_id not in catalog():
            abort(404)
        new_id = None
        if request.method == 'POST':
            upload = request.files.get('marquee')
            if not upload or not upload.filename:
                raise ValueError('Choose a marquee image from your device.')
            upload.stream.seek(0, 2)
            if upload.stream.tell() > 40 * 1024 * 1024:
                raise ValueError('Choose an image under 40 MB.')
            upload.stream.seek(0)
            try:
                with Image.open(upload.stream) as image:
                    if image.format not in {'JPEG', 'PNG', 'WEBP', 'HEIF'}:
                        raise ValueError('Choose a JPG, PNG, WebP or iPhone HEIC image.')
                    if image.width * image.height > 64_000_000:
                        raise ValueError('Choose an image under 64 megapixels.')
                    image = ImageOps.exif_transpose(image)
                    image.thumbnail((1600, 1600))
                    clean = Image.new('RGBA', image.size)
                    clean.paste(image.convert('RGBA'))
                    new_id = str(uuid.uuid4())
                    clean.save(marquees / (new_id + '.png'), format='PNG')
            except (Image.DecompressionBombError, Image.DecompressionBombWarning):
                raise ValueError('Choose an image under 64 megapixels.')
            except (UnidentifiedImageError, OSError, SyntaxError):
                raise ValueError('That image could not be opened. Choose a JPG, PNG, WebP or iPhone HEIC image.')
            expected = request.form.get('expectedMarqueeId')
        else:
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                raise ValueError('Choose the current marquee before restoring the default.')
            expected = payload.get('expectedMarqueeId')
        try:
            with get_db() as db:
                db.execute('BEGIN IMMEDIATE')
                current = db.execute('SELECT marquee_id FROM games WHERE id=?', (game_id,)).fetchone()[0]
                if expected != (current or ''):
                    abort(409, 'The marquee changed on another device. Close this window and try again.')
                db.execute('UPDATE games SET marquee_id=? WHERE id=?', (new_id, game_id))
                db.execute('INSERT INTO marquee_audit (game_id,actor,previous_id,next_id,created_at) VALUES (?,?,?,?,?)',
                           (game_id, g.user['sub'], current, new_id, int(time.time())))
        except Exception:
            if new_id:
                (marquees / (new_id + '.png')).unlink(missing_ok=True)
            raise
        return jsonify(ok=True, marqueeId=new_id)

    @app.get('/api/game-catalog')
    def search_game_catalog():
        query = game_key(request.args.get('q', ''))
        matches = [entry for entry in artwork_catalog.values() if query in game_key(entry['title']) or query in game_key(entry['id'])]
        owned = {game_key(game['title']) for game in catalog().values() if game['eligible']}
        overrides = {game_key(game['title']): game['marqueeId'] for game in catalog().values() if game['marqueeId']}
        return jsonify(total=len(matches), games=[entry | {'inArcade': game_key(entry['title']) in owned, 'marqueeId': overrides.get(game_key(entry['title']))} for entry in matches[:40]])

    @app.patch('/api/admin/games/<game_id>')
    @authenticated(admin=True)
    def set_game_eligibility(game_id):
        payload = request.get_json(silent=True)
        if game_id not in catalog() or not isinstance(payload, dict) or type(payload.get('eligible')) is not bool:
            raise ValueError('Choose a game and whether it belongs in the arcade.')
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            if not payload['eligible'] and catalog()[game_id]['eligible'] and db.execute('SELECT COUNT(*) FROM games WHERE eligible=1').fetchone()[0] <= 1:
                raise ValueError('Keep at least one game in the arcade.')
            db.execute('UPDATE games SET eligible=? WHERE id=?', (int(payload['eligible']), game_id))
        return jsonify(ok=True)

    @app.patch('/api/admin/games/<game_id>/name')
    @authenticated(admin=True)
    def rename_game(game_id):
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or not isinstance(payload.get('title'), str):
            raise ValueError('Enter a game name.')
        title = ' '.join(payload['title'].split())
        key = game_key(title)
        if not 2 <= len(title) <= 250 or not key or any(unicodedata.category(c).startswith('C') for c in title):
            raise ValueError('Enter a game name between 2 and 250 characters.')
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            current = db.execute('SELECT title FROM games WHERE id=?', (game_id,)).fetchone()
            if not current:
                abort(404)
            if payload.get('expectedTitle') != current['title']:
                abort(409, 'This game was renamed on another device. Reopen it before saving.')
            if db.execute('SELECT 1 FROM games WHERE search_key=? AND id!=?', (key, game_id)).fetchone():
                abort(409, 'A game with that name already exists. Renaming does not merge games.')
            db.execute('UPDATE games SET title=?,search_key=? WHERE id=?', (title, key, game_id))
        return jsonify(ok=True, title=title)

    @app.patch('/api/admin/games/<game_id>/leaderboard')
    @authenticated(admin=True)
    def set_leaderboard_visibility(game_id):
        payload = request.get_json(silent=True)
        if game_id not in catalog() or not isinstance(payload, dict) or type(payload.get('showOnLeaderboard')) is not bool:
            raise ValueError('Choose a game and whether to show it on the leaderboard.')
        with get_db() as db:
            db.execute('UPDATE games SET show_on_leaderboard=? WHERE id=?', (int(payload['showOnLeaderboard']), game_id))
        return jsonify(ok=True)

    @app.post('/api/admin/games')
    @authenticated(admin=True)
    def add_arcade_game():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            raise ValueError('Enter a game title and score type.')
        picked = artwork_catalog.get(payload.get('catalogId'))
        if payload.get('catalogId') and not picked:
            raise ValueError('Choose a valid game from the marquee catalog.')
        title = picked['title'] if picked else ' '.join(str(payload.get('title', '')).split())
        key = game_key(title)
        kind = payload.get('kind', picked['kind'] if picked else 'points')
        if not 2 <= len(title) <= (250 if picked else 80) or not key or any(unicodedata.category(c).startswith('C') for c in title):
            raise ValueError('Enter a game name between 2 and 80 characters.')
        if kind not in {'points', 'time'}:
            raise ValueError('Choose points or fastest time.')
        db = get_db()
        with db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM games WHERE search_key=?', (key,)).fetchone()
            if existing:
                if existing['kind'] != kind:
                    raise ValueError('This game already exists with a different score type.')
                game_id = existing['id']
            else:
                game_id = 'custom-' + hashlib.sha256(key.encode()).hexdigest()[:24]
                if db.execute('SELECT 1 FROM games WHERE id=?', (game_id,)).fetchone():
                    game_id = 'custom-' + uuid.uuid4().hex[:24]
                db.execute('INSERT INTO games (id,title,search_key,image,kind,sort_order) VALUES (?,?,?,?,?,?)', (game_id, title, key, 'images/new-game.svg', kind, 1000))
            db.execute('UPDATE games SET eligible=1 WHERE id=?', (game_id,))
            if picked:
                db.execute('UPDATE games SET image=? WHERE id=?', (picked['image'], game_id))
        g.pop('catalog', None)
        return jsonify(game=catalog()[game_id], alreadyExists=bool(existing)), 200 if existing else 201

    @app.get('/api/admin/scores')
    @authenticated(admin=True)
    def admin_scores():
        game_id = request.args.get('gameId')
        if game_id not in catalog():
            raise ValueError('Choose a game to review its submissions.')
        rows = get_db().execute('SELECT * FROM scores WHERE game_id=? ORDER BY deleted_at IS NOT NULL, created_at DESC, id DESC LIMIT 200', (game_id,)).fetchall()
        # Activity captures whether the submission actually broke the record then.
        # Recover its original value from the first correction audit, not today's value.
        history_rows = get_db().execute('''SELECT s.*, a.is_record,
            (SELECT before_json FROM audit WHERE score_id=s.id AND action='correct' ORDER BY id LIMIT 1) AS original_json
            FROM scores s LEFT JOIN activity a ON a.score_id=s.id
            WHERE s.game_id=? AND (a.is_record=1 OR s.created_at=0)
            ORDER BY s.created_at DESC, a.id DESC, s.id DESC''', (game_id,)).fetchall()
        history = []
        for row in history_rows:
            original = json.loads(row['original_json']) if row['original_json'] else dict(row)
            history.append({'id': row['id'], 'score': display_score(original['value'], catalog()[game_id]['kind']),
                            'initials': original['initials'], 'email': row['user_email'] or None,
                            'createdAt': row['created_at'] or None, 'imported': row['created_at'] == 0,
                            'corrected': bool(row['original_json']), 'deleted': row['deleted_at'] is not None})
        untracked = get_db().execute('''SELECT COUNT(*) FROM scores s LEFT JOIN activity a ON a.score_id=s.id
            WHERE s.game_id=? AND s.created_at>0 AND a.id IS NULL''', (game_id,)).fetchone()[0]
        return jsonify(scores=[public_record(row) | {'email': row['user_email'] or 'Imported starting record', 'deleted': row['deleted_at'] is not None} for row in rows], recordHistory=history, untrackedSubmissions=untracked)

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
                value = score_value(payload.get('score', ''), catalog()[row['game_id']]['kind'])
                initials = str(payload.get('initials', '')).upper().strip()
                if not re.fullmatch('[A-Z]{3}', initials):
                    raise ValueError('Enter exactly three letters.')
                db.execute('UPDATE scores SET value=?,initials=?,taunt=?,revision=revision+1 WHERE id=?', (value, initials, clean_taunt(payload.get('taunt', row['taunt'])), score_id))
                action = 'correct'
            after = db.execute('SELECT * FROM scores WHERE id=?', (score_id,)).fetchone()
            db.execute('INSERT INTO audit (score_id,actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?,?)',
                       (score_id, g.user['sub'], action, json.dumps(dict(row)), json.dumps(dict(after)), int(time.time())))
        return jsonify(ok=True)

    @app.get('/api/admin/export')
    @authenticated(admin=True)
    def export():
        response = jsonify(games=list(catalog().values()), scores=[dict(row) for row in get_db().execute('SELECT * FROM scores')], audit=[dict(row) for row in get_db().execute('SELECT * FROM audit')])
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

    cabinets.register(app, get_db, authenticated, data, game_key)
    inventory_import.register(app, get_db, authenticated, game_key)
    return app


if __name__ == '__main__':
    demo = os.environ.get('ARCADE_DEMO') == '1'
    port = int(os.environ.get('PORT', '4173'))
    if demo:
        os.environ.setdefault('ARCADE_DATA_DIR', str(ROOT / '.local-preview'))
        os.environ.setdefault('ARCADE_ALLOWED_ORIGINS', f'http://127.0.0.1:{port},http://localhost:{port}')
        os.environ.setdefault('ARCADE_PUBLIC_URL', f'http://127.0.0.1:{port}/')
    create_app(allow_demo=True).run(host='127.0.0.1', port=port, debug=False)
