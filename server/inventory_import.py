"""Preview-first, additive CSV inventory import. Never imports or changes scores."""
import csv
import hashlib
import io
import json
import unicodedata
from flask import abort, g, jsonify, request


def plan(db, text, key):
    if not isinstance(text, str) or len(text.encode('utf-8')) > 262144:
        raise ValueError('Choose a UTF-8 CSV under 256 KB.')
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), strict=True)
        allowed = {'Game', 'Cabinet 1', 'Cabinet 2', 'Cabinet 3', 'Cabinet 4', 'Scoring'}
        if not reader.fieldnames or 'Game' not in reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or set(reader.fieldnames) - allowed:
            raise ValueError('Use the template headers: Game, Cabinet 1, Cabinet 2, Cabinet 3, Cabinet 4, Scoring. Scores are not imported.')
        source = []
        for number, row in enumerate(reader, 2):
            if number > 501:
                raise ValueError('Import at most 500 rows at a time.')
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'Row {number}: the number of columns does not match the headers.')
            if any(v.strip() for v in row.values()):
                source.append((number, row))
    except csv.Error as exc:
        raise ValueError('The CSV could not be read. Export it again as CSV UTF-8.') from exc
    if not source:
        raise ValueError('Add at least one game below the template headers.')
    games = {r['search_key']: dict(r) for r in db.execute('SELECT id,title,search_key,kind,eligible FROM games')}
    cabinets = {r['name_key']: dict(r) for r in db.execute('SELECT id,name,name_key FROM cabinets')}
    links = {tuple(r) for r in db.execute('SELECT cabinet_id,game_id FROM cabinet_games')}
    new_games, new_cabinets, new_links, rows, errors = {}, {}, set(), [], []

    def name(value, limit, label):
        value = ' '.join(value.split())
        if not 2 <= len(value) <= limit or not key(value) or any(unicodedata.category(c).startswith('C') for c in value) or value.startswith(('=', '+', '-', '@')):
            raise ValueError(f'{label} must be 2–{limit} characters, without formulas or control characters.')
        return value

    for number, row in source:
        try:
            title = name(row['Game'], 100, 'Game')
            gkey = key(title)
            game = games.get(gkey) or new_games.get(gkey)
            kind = row.get('Scoring', '').strip().lower() or (game['kind'] if game else 'points')
            if kind not in {'points', 'time'}:
                raise ValueError('Scoring must be points or time (or blank).')
            if game and game['kind'] != kind:
                raise ValueError(f"{game['title']} already uses {game['kind']} scoring. Correct this row; existing scoring cannot be changed by import.")
            names = [name(row.get(f'Cabinet {i}', ''), 80, 'Cabinet') for i in range(1, 5) if row.get(f'Cabinet {i}', '').strip()]
            if not game:
                game = dict(id='custom-'+hashlib.sha256(gkey.encode()).hexdigest()[:24], title=title, search_key=gkey, kind=kind, eligible=1)
                new_games[gkey] = game
            chosen = []
            for title in names:
                ckey = key(title)
                cabinet = cabinets.get(ckey) or new_cabinets.get(ckey)
                if not cabinet:
                    cabinet = dict(id='import-'+hashlib.sha256(ckey.encode()).hexdigest()[:24], name=title, name_key=ckey)
                    new_cabinets[ckey] = cabinet
                pair = (cabinet['id'], game['id'])
                if pair not in links:
                    new_links.add(pair)
                if cabinet['name'] not in chosen:
                    chosen.append(cabinet['name'])
            rows.append(dict(row=number, id=game['id'], title=game['title'], kind=kind, eligible=game['eligible'], cabinets=chosen, action='Reuse game' if gkey in games else 'Add game'))
        except ValueError as exc:
            errors.append(f'Row {number}: {exc}')
    result = dict(rows=rows, errors=errors, games=list(new_games.values()), cabinets=list(new_cabinets.values()), links=sorted(new_links))
    result['counts'] = dict(games=len(new_games), cabinets=len(new_cabinets), assignments=len(new_links))
    result['previewHash'] = hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()
    return result


def register(app, get_db, authenticated, key):
    @app.post('/api/admin/inventory-import')
    @authenticated(admin=True)
    def import_inventory():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or payload.get('mode') not in {'preview', 'commit'}:
            raise ValueError('Choose preview or commit.')
        with get_db() as db:
            db.execute('BEGIN IMMEDIATE' if payload['mode']=='commit' else 'BEGIN')
            result = plan(db, payload.get('csv'), key)
            if payload['mode'] == 'preview':
                return jsonify(result)
            if result['errors']:
                raise ValueError('Correct all row errors before importing.')
            if payload.get('previewHash') != result['previewHash']:
                abort(409, 'The collection or file changed. Preview the import again before saving.')
            for c in result['cabinets']:
                db.execute('INSERT INTO cabinets(id,name,name_key) VALUES (?,?,?)', (c['id'],c['name'],c['name_key']))
            for game in result['games']:
                db.execute('INSERT INTO games(id,title,search_key,image,kind,sort_order,eligible) VALUES (?,?,?,?,?,1000,1)', (game['id'],game['title'],game['search_key'],'images/new-game.svg',game['kind']))
            db.executemany('INSERT INTO cabinet_games(cabinet_id,game_id) VALUES (?,?)', result['links'])
            if any(result['counts'].values()):
                import time
                db.execute('INSERT INTO cabinet_audit(actor,action,before_json,after_json,created_at) VALUES (?,?,?,?,?)', (g.user['sub'],'import','{}',json.dumps(result),int(time.time())))
        return jsonify(counts=result['counts'], imported=True)
