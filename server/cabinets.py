"""Shared cabinet inventory. Assignments never mutate game eligibility or scores."""
import json
import hashlib
import time
import unicodedata
import uuid
from flask import abort, g, jsonify, request, send_from_directory
from PIL import Image, ImageOps, UnidentifiedImageError


def initialize(db, seed_path, game_key):
    db.executescript('''
      CREATE TABLE IF NOT EXISTS cabinets (id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE, code TEXT NOT NULL DEFAULT '', photo_id TEXT, revision INTEGER NOT NULL DEFAULT 1);
      CREATE TABLE IF NOT EXISTS cabinet_games (cabinet_id TEXT NOT NULL REFERENCES cabinets(id) ON DELETE CASCADE, game_id TEXT NOT NULL REFERENCES games(id), PRIMARY KEY(cabinet_id,game_id));
      CREATE TABLE IF NOT EXISTS cabinet_audit (id INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, before_json TEXT NOT NULL, after_json TEXT NOT NULL, created_at INTEGER NOT NULL);
    ''')
    with db:
        db.execute('BEGIN IMMEDIATE')
        seed = json.loads(seed_path.read_text())
        known = {game_key(r['title']): r['id'] for r in db.execute('SELECT id,title FROM games')}
        if not db.execute("SELECT 1 FROM metadata WHERE key='cabinet_seed_v1'").fetchone():
            for cabinet in seed:
                cid = 'nick-' + cabinet['code'].lower()
                db.execute('INSERT INTO cabinets(id,name,name_key,code) VALUES (?,?,?,?)', (cid,cabinet['name'],game_key(cabinet['name']),cabinet['code']))
                for title in cabinet['games']:
                    if game_key(title) in known:
                        db.execute('INSERT OR IGNORE INTO cabinet_games VALUES (?,?)', (cid,known[game_key(title)]))
            db.execute("INSERT INTO metadata VALUES ('cabinet_seed_v1','1')")
        if db.execute("SELECT 1 FROM metadata WHERE key='cabinet_games_v2'").fetchone():
            return
        # Reviewed spelling/title equivalents only. Nintendo Vs. editions stay
        # separate from ambiguous legacy Nintendo titles and keep their scores.
        aliases = {
            game_key('Donkey Kong Jr.'): 'Donkey Kong Junior',
            game_key('Street Fighter II'): 'Street Fighter II The World Warrior',
            game_key("Street Fighter II' Champion Edition"): 'Street Fighter II Champion Edition',
            game_key("Turbo Street Fighter II' Hyper Fighting"): 'Street Fighter II Hyper Fighting',
            game_key("Dragon's Lair II"): "Dragon's Lair II: Time Warp",
        }
        edited = {json.loads(r[0]).get('gameId') for r in db.execute("SELECT after_json FROM cabinet_audit WHERE action='assign'")}
        existing_cabinets = {r[0] for r in db.execute('SELECT id FROM cabinets')}
        for cabinet in seed:
            cid = 'nick-' + cabinet['code'].lower()
            if cid not in existing_cabinets:
                continue
            for title in cabinet['games']:
                canonical = aliases.get(game_key(title), title)
                key = game_key(canonical)
                gid = known.get(key) or known.get(game_key(title))
                if not gid:
                    gid = 'custom-' + hashlib.sha256(key.encode()).hexdigest()[:24]
                    db.execute('INSERT INTO games(id,title,search_key,image,kind,sort_order,eligible) VALUES (?,?,?,?,?,?,1)',
                               (gid,canonical,key,'images/new-game.svg','points',1000))
                known[key] = gid
                if gid not in edited:
                    db.execute('INSERT OR IGNORE INTO cabinet_games VALUES (?,?)',(cid,gid))
        db.execute("INSERT INTO metadata VALUES ('cabinet_games_v2','1')")


def register(app, get_db, authenticated, data, game_key):
    images = data / 'cabinets'
    images.mkdir(exist_ok=True, mode=0o700)

    def rows():
        return [dict(r) | {'gameIds': [g[0] for g in get_db().execute('SELECT game_id FROM cabinet_games WHERE cabinet_id=? ORDER BY game_id', (r['id'],))]} for r in get_db().execute('SELECT id,name,code,photo_id AS photoId,revision FROM cabinets ORDER BY name COLLATE NOCASE')]

    def audit(db, action, before, after):
        db.execute('INSERT INTO cabinet_audit(actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?)', (g.user['sub'],action,json.dumps(before),json.dumps(after),int(time.time())))

    def current(db, cid, revision):
        row = db.execute('SELECT * FROM cabinets WHERE id=?', (cid,)).fetchone()
        if not row:
            abort(404)
        if type(revision) is not int or revision != row['revision']:
            abort(409, 'This cabinet changed on another device. Reopen it before saving.')
        return dict(row)

    def payload():
        p = request.get_json(silent=True)
        if not isinstance(p, dict):
            raise ValueError('Provide cabinet details.')
        return p

    @app.get('/api/admin/cabinets')
    @authenticated(admin=True)
    def list_cabinets():
        return jsonify(cabinets=rows())

    @app.post('/api/admin/cabinets')
    @app.patch('/api/admin/cabinets/<cid>')
    @authenticated(admin=True)
    def save_cabinet(cid=None):
        p = payload()
        name = ' '.join(str(p.get('name','')).split())
        if not 2 <= len(name) <= 80 or not game_key(name) or any(unicodedata.category(c).startswith('C') for c in name):
            raise ValueError('Choose a cabinet name between 2 and 80 characters.')
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            before = current(db,cid,p.get('revision')) if cid else None
            if db.execute('SELECT 1 FROM cabinets WHERE name_key=? AND id!=?', (game_key(name),cid or '')).fetchone():
                abort(409, 'A cabinet with that name already exists.')
            if cid:
                db.execute('UPDATE cabinets SET name=?,name_key=?,revision=revision+1 WHERE id=?', (name,game_key(name),cid))
            else:
                cid = str(uuid.uuid4())
                db.execute('INSERT INTO cabinets(id,name,name_key) VALUES (?,?,?)', (cid,name,game_key(name)))
            audit(db,'save',before,{'id':cid,'name':name})
        return jsonify(cabinets=rows(),id=cid)

    @app.put('/api/admin/games/<gid>/cabinets')
    @authenticated(admin=True)
    def assign_game(gid):
        p = payload()
        selected, expected = p.get('cabinetIds'), p.get('expectedCabinetIds')
        if not isinstance(selected,list) or not isinstance(expected,list) or any(not isinstance(v,str) for v in selected + expected) or len(selected)>200 or len(set(selected))!=len(selected):
            raise ValueError('Choose valid cabinets.')
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM games WHERE id=?',(gid,)).fetchone():
                abort(404)
            old = sorted(r[0] for r in db.execute('SELECT cabinet_id FROM cabinet_games WHERE game_id=?',(gid,)))
            if old != sorted(expected):
                abort(409,'Assignments changed on another device. Reopen the picker before saving.')
            valid = {r[0] for r in db.execute('SELECT id FROM cabinets')}
            if not set(selected) <= valid:
                raise ValueError('One of these cabinets no longer exists.')
            db.execute('DELETE FROM cabinet_games WHERE game_id=?',(gid,))
            db.executemany('INSERT INTO cabinet_games VALUES (?,?)',[(cid,gid) for cid in selected])
            audit(db,'assign',{'gameId':gid,'cabinetIds':old},{'gameId':gid,'cabinetIds':selected})
        return jsonify(cabinets=rows())

    @app.post('/api/admin/cabinets/<cid>/photo')
    @authenticated(admin=True)
    def upload_cabinet_photo(cid):
        upload = request.files.get('photo')
        if not upload or not upload.filename:
            raise ValueError('Choose a cabinet photo.')
        upload.stream.seek(0,2)
        if upload.stream.tell() > 40*1024*1024:
            raise ValueError('Choose a photo under 40 MB.')
        upload.stream.seek(0)
        new_id = str(uuid.uuid4())
        try:
            with Image.open(upload.stream) as im:
                if im.format not in {'JPEG','PNG','WEBP','HEIF'} or im.width*im.height > 64_000_000:
                    raise ValueError('Choose JPG, PNG, WebP or HEIC under 64 megapixels.')
                im = ImageOps.exif_transpose(im)
                im.thumbnail((1200,1200))
                clean = Image.new('RGB', im.size, '#fffbed')
                rgba = im.convert('RGBA')
                clean.paste(rgba,mask=rgba.getchannel('A'))
                clean.save(images / (new_id+'.jpg'),quality=88)
            with get_db() as db:
                db.execute('BEGIN IMMEDIATE')
                try:
                    revision = int(request.form.get('revision',''))
                except ValueError:
                    abort(409,'Reopen this cabinet before saving.')
                before = current(db,cid,revision)
                db.execute('UPDATE cabinets SET photo_id=?,revision=revision+1 WHERE id=?',(new_id,cid))
                audit(db,'photo',before,{'id':cid,'photo_id':new_id})
        except (UnidentifiedImageError,OSError,SyntaxError,Image.DecompressionBombError,Image.DecompressionBombWarning):
            (images/(new_id+'.jpg')).unlink(missing_ok=True)
            raise ValueError('That photo could not be read. Choose JPG, PNG, WebP or iPhone HEIC under 40 MB and 64 megapixels.')
        except Exception:
            (images/(new_id+'.jpg')).unlink(missing_ok=True)
            raise
        return jsonify(cabinets=rows())

    @app.get('/api/cabinet-photos/<photo_id>')
    def cabinet_photo(photo_id):
        if not get_db().execute('SELECT 1 FROM cabinets WHERE photo_id=?',(photo_id,)).fetchone():
            abort(404)
        return send_from_directory(images,photo_id+'.jpg',mimetype='image/jpeg')
