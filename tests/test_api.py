import io
import json
import sqlite3
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from PIL import Image
from server.app import create_app, score_value


def identity(token):
    if token not in {'player', 'admin', 'unverified', 'outsider'}:
        raise ValueError('Invalid test identity')
    return {'sub': token, 'email': 'ronavis@gmail.com' if token == 'admin' else 'player@gmail.com', 'email_verified': token != 'unverified'}


@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False, 'TEST_TOKEN_VERIFIER': identity})


def headers(token='player'):
    return {'Authorization': 'Bearer ' + token, 'Origin': 'https://ronavis.github.io'}


def submit(client, score='42500', initials='RON', game='galaga', token='player', **extra):
    data = dict(gameId=game, score=score, initials=initials, requestId=str(uuid.uuid4()))
    data.update(extra)
    return client.post('/api/scores', data=data, headers=headers(token))


def record(client, game='galaga'):
    return next(g['record'] for g in client.get('/api/leaderboard').json['games'] if g['id'] == game)


def test_persistence_and_cross_client_visibility(app):
    phone, tv = app.test_client(), app.test_client()
    assert record(tv)['score'] == '41,510'
    result = submit(phone)
    assert result.status_code == 201 and result.json['isRecord']
    assert record(tv)['score'] == '42,500'
    reopened = create_app(dict(app.config)).test_client()
    assert record(reopened)['score'] == '42,500'
    assert len(reopened.get('/api/leaderboard').json['games']) == 33


def test_lower_scores_are_history_not_replacements(app):
    c = app.test_client()
    assert submit(c, '100').json['isRecord'] is False
    assert record(c)['score'] == '41,510'
    scores = c.get('/api/admin/scores?gameId=galaga', headers=headers('admin')).json['scores']
    assert any(s['score'] == '100' for s in scores)


def test_ties_preserve_earlier_record(app):
    c = app.test_client()
    assert submit(c, '41510').json['isRecord'] is False
    assert record(c)['initials'] == 'JJH'


def test_time_records_sort_ascending(app):
    c = app.test_client()
    assert record(c, 'vsexcitebike')['score'] == '1:02.30'
    assert submit(c, '1:01.29', game='vsexcitebike').json['isRecord']
    assert not submit(c, '1:03.00', game='vsexcitebike').json['isRecord']
    assert record(c, 'vsexcitebike')['score'] == '1:01.29'


@pytest.mark.parametrize('score', ['-1', '0', '12abc', '1.5', '1e6', 'NaN', '1,23', '10000000000'])
def test_invalid_scores_rejected(app, score):
    c = app.test_client()
    assert submit(c, score).status_code == 400
    assert record(c)['score'] == '41,510'


@pytest.mark.parametrize('initials', ['', 'AB', 'ABCD', '<X>', '😎ON'])
def test_invalid_initials_rejected(app, initials):
    assert submit(app.test_client(), initials=initials).status_code == 400


def test_no_auth_forged_token_and_unverified_identity_rejected(app):
    c = app.test_client()
    assert c.post('/api/scores').status_code == 401
    assert submit(c, token='fake').status_code == 401
    assert submit(c, token='unverified').status_code == 401
    assert c.get('/api/admin/export', headers=headers()).status_code == 403
    assert c.get('/api/admin/scores?gameId=galaga', headers=headers()).status_code == 403
    assert '/api/demo-session' not in {rule.rule for rule in app.url_map.iter_rules()}
    assert c.post('/api/demo-session', json={'role': 'admin'}).status_code in {404, 405}


def test_idempotent_retry_and_conflicting_retry(app):
    c = app.test_client(); key = str(uuid.uuid4())
    first = submit(c, requestId=key)
    retry = submit(c, requestId=key)
    assert first.status_code == 201 and retry.status_code == 200
    assert first.json['record']['id'] == retry.json['record']['id']
    assert submit(c, '50000', requestId=key).status_code == 409


def test_admin_correction_deletion_and_audit(app):
    c = app.test_client(); top = submit(c).json['record']
    body = {'revision': 1, 'score': '43000', 'initials': 'ABC'}
    url = '/api/admin/scores/' + top['id']
    assert c.patch(url, json=body, headers=headers()).status_code == 403
    assert c.delete(url, json={'revision': 1}, headers=headers()).status_code == 403
    assert c.patch(url, json=body, headers=headers('admin')).status_code == 200
    assert record(c)['score'] == '43,000'
    assert c.patch(url, json=body, headers=headers('admin')).status_code == 409
    assert c.delete(url, json={'revision': 2}, headers=headers('admin')).status_code == 200
    assert record(c)['score'] == '41,510'
    exported = c.get('/api/admin/export', headers=headers('admin')).json
    assert [a['action'] for a in exported['audit']] == ['correct', 'remove']
    assert any(s['deleted_at'] for s in exported['scores'])


def test_photo_reencoded_protected_and_removed(app):
    c = app.test_client(); buf = io.BytesIO()
    im = Image.new('RGB', (2000, 1000), '#13d5df'); im.save(buf, format='PNG'); buf.seek(0)
    result = submit(c, photo=(buf, '../../bad.html'))
    assert result.status_code == 201
    r = result.json['record']; url = '/api/photos/' + r['photoId']
    assert c.get(url).status_code == 401
    photo = c.get(url, headers=headers())
    assert photo.status_code == 200 and photo.mimetype == 'image/jpeg'
    image = Image.open(io.BytesIO(photo.data))
    assert image.size == (1600, 800) and not image.getexif()
    c.delete('/api/admin/scores/' + r['id'], json={'revision': 1}, headers=headers('admin'))
    assert c.get(url, headers=headers()).status_code == 404


def test_non_image_upload_rejected(app):
    c = app.test_client()
    assert submit(c, photo=(io.BytesIO(b'<script>alert(1)</script>'), 'photo.jpg')).status_code == 400
    assert record(c)['score'] == '41,510'


def test_cors_and_privacy(app):
    c = app.test_client()
    response = c.get('/api/leaderboard', headers={'Origin': 'https://ronavis.github.io'})
    assert response.headers['Access-Control-Allow-Origin'] == 'https://ronavis.github.io'
    assert 'email' not in response.text and 'user_sub' not in response.text
    assert c.get('/api/leaderboard', headers={'Origin': 'https://evil.example'}).status_code == 403
    assert c.get('/api/admin/export', headers=headers('admin')).headers['Cache-Control'] == 'no-store'
    assert c.get('/server/app.py').status_code == 404
    assert c.get('/.env').status_code == 404


def test_rate_limit(app):
    c = app.test_client()
    for _ in range(5):
        assert submit(c).status_code == 201
    assert submit(c).status_code == 429


def test_concurrent_submissions_choose_best(app):
    def post(score):
        return submit(app.test_client(), str(score)).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(post, [49000, 45000, 60000, 47000])) == [201] * 4
    assert record(app.test_client())['score'] == '60,000'


def test_demo_cannot_start_in_production(app, monkeypatch):
    monkeypatch.setenv('ARCADE_DEMO', '1')
    with pytest.raises(RuntimeError, match='loopback'):
        create_app({'DATA_DIR': app.config['DATA_DIR']})


def test_demo_rejects_remote_address_and_host(tmp_path):
    a = create_app({'DATA_DIR': str(tmp_path), 'DEMO': True}, allow_demo=True)
    c = a.test_client()
    assert c.post('/api/demo-session', json={}, environ_base={'REMOTE_ADDR': '8.8.8.8'}).status_code == 403
    assert c.post('/api/demo-session', json={}, headers={'Host': 'evil.example'}).status_code == 403


def test_real_google_verifier_rejects_invalid_token(app, monkeypatch):
    import server.app as module
    monkeypatch.setattr(module.id_token, '_fetch_certs', lambda *a, **k: {})
    app.config.pop('TEST_TOKEN_VERIFIER')
    assert app.test_client().get('/api/session', headers=headers('not.a.jwt')).status_code == 401


@pytest.mark.parametrize('override,status', [({}, 200), ({'aud': 'wrong-client'}, 401), ({'exp': 1}, 401), ({'iss': 'https://evil.example'}, 401), ({'email_verified': False}, 401)])
def test_google_signature_audience_expiry_and_issuer(app, monkeypatch, override, status):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from google.auth import jwt, crypt
    import server.app as module
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    monkeypatch.setattr(module.id_token, '_fetch_certs', lambda *a, **k: {'fixture': public})
    claims = {'sub': 'signed-fixture', 'email': 'ronavis@gmail.com', 'email_verified': True,
              'iss': 'https://accounts.google.com', 'aud': app.config['GOOGLE_CLIENT_ID'], 'iat': int(time.time()) - 5, 'exp': int(time.time()) + 300}
    claims.update(override)
    token = jwt.encode(crypt.RSASigner.from_string(private, key_id='fixture'), claims).decode()
    app.config.pop('TEST_TOKEN_VERIFIER')
    response = app.test_client().get('/api/session', headers=headers(token))
    assert response.status_code == status
    if status == 200:
        assert response.json['admin'] is True


def test_oversize_upload_is_rejected(app):
    assert submit(app.test_client(), photo=(io.BytesIO(b'x' * (42 * 1024 * 1024)), 'test.png')).status_code == 413


def test_third_party_email_cannot_gain_admin_by_email_alone(app):
    app.config['ADMIN_EMAILS'] = {'owner@example.com'}
    app.config['TEST_TOKEN_VERIFIER'] = lambda _: {'sub': 'foreign', 'email': 'owner@example.com', 'email_verified': True}
    assert app.test_client().get('/api/session', headers=headers()).json['admin'] is False


def test_backup_restores_scores_and_photos(app, tmp_path):
    from scripts.backup import backup
    client = app.test_client()
    photo = io.BytesIO()
    Image.new('RGB', (40, 40), 'red').save(photo, format='PNG')
    photo.seek(0)
    created = submit(client, photo=(photo, 'proof.png'))
    assert created.status_code == 201
    destination = tmp_path.parent / (tmp_path.name + '-backup')
    backup(app.config['DATA_DIR'], destination)
    assert (destination / 'COMPLETE').is_file()
    restored = create_app(dict(app.config) | {'DATA_DIR': str(destination)}).test_client()
    assert record(restored)['score'] == '42,500'
    photo_id = created.json['record']['photoId']
    assert restored.get('/api/photos/' + photo_id, headers=headers()).status_code == 200
    with pytest.raises(FileExistsError):
        backup(app.config['DATA_DIR'], destination)


def test_invalid_admin_json_does_not_crash(app):
    c = app.test_client()
    score_id = record(c)['id']
    assert c.patch('/api/admin/scores/' + score_id, json=['bad'], headers=headers('admin')).status_code == 400


def test_simpsons_first_score_and_all_catalog_games(app):
    c = app.test_client()
    games = c.get('/api/leaderboard').json['games']
    assert len({g['id'] for g in games}) == 33
    assert record(c, 'simpsons') is None
    for index, game in enumerate(games):
        app.config['TEST_TOKEN_VERIFIER'] = lambda token: dict(sub=token, email='player@gmail.com', email_verified=True)
        result = submit(c, '0:59.00' if game['kind'] == 'time' else '100', game=game['id'], token=f'player{index}')
        assert result.status_code == 201, (game['title'], result.json)
        if game['id'] == 'simpsons':
            assert result.json['isRecord'] is True


def test_new_game_atomic_persistent_searchable_and_admin(app):
    c = app.test_client()
    result = submit(c, '123', game='', gameTitle='  New Arcade Game  ', gameKind='points')
    assert result.status_code == 201 and result.json['isRecord']
    game_id = result.json['game']['id']
    second = submit(c, '100', game='', gameTitle='New-Arcade Game', gameKind='points')
    assert second.status_code == 201 and second.json['game']['id'] == game_id
    reopened = create_app(dict(app.config)).test_client()
    assert record(reopened, game_id)['score'] == '123'
    saved = reopened.get('/api/admin/scores?gameId=' + game_id, headers=headers('admin')).json['scores']
    assert len(saved) == 2
    correction = reopened.patch('/api/admin/scores/' + result.json['record']['id'], json=dict(score='200', initials='ABC', revision=1), headers=headers('admin'))
    assert correction.status_code == 200
    assert record(c, game_id)['score'] == '200'


def test_failed_new_game_does_not_leave_empty_catalog_entry(app):
    c = app.test_client()
    result = submit(c, game='', gameTitle='Unfinished Game', photo=(io.BytesIO(b'broken'), 'bad.heic'))
    assert result.status_code == 400
    assert not any(g['title'] == 'Unfinished Game' for g in c.get('/api/leaderboard').json['games'])


def test_new_time_game_and_conflicting_kind(app):
    c = app.test_client()
    result = submit(c, '1:02.30', game='', gameTitle='New Racing Game', gameKind='time')
    assert result.status_code == 201 and result.json['isRecord']
    assert submit(c, '500', game='', gameTitle='New Racing Game', gameKind='points').status_code == 400
    assert submit(c, '0:59.99', game=result.json['game']['id']).json['isRecord']


def test_iphone_heic_reencoded_and_metadata_removed(app):
    image = Image.new('RGB', (1200, 600), 'blue')
    exif = Image.Exif(); exif[270] = 'private'; exif[274] = 6
    source = io.BytesIO()
    image.save(source, format='HEIF', exif=exif)
    source.seek(0)
    c = app.test_client()
    response = submit(c, photo=(source, 'IMG_0001.HEIC'))
    assert response.status_code == 201, response.json
    saved = c.get('/api/photos/' + response.json['record']['photoId'], headers=headers())
    decoded = Image.open(io.BytesIO(saved.data))
    assert decoded.format == 'JPEG' and max(decoded.size) <= 1600
    assert not decoded.getexif()


def test_48_megapixel_camera_photo_is_resized(app):
    source = io.BytesIO()
    Image.new('RGB', (8064, 6048), 'green').save(source, format='JPEG')
    source.seek(0)
    c = app.test_client()
    response = submit(c, photo=(source, 'IMG_48MP.JPG'))
    assert response.status_code == 201, response.json
    saved = c.get('/api/photos/' + response.json['record']['photoId'], headers=headers())
    assert Image.open(io.BytesIO(saved.data)).size == (1600, 1200)


def test_photo_over_old_eight_mb_limit(app):
    source = io.BytesIO()
    Image.new('RGB', (40, 40)).save(source, format='PNG')
    source.write(b'\0' * (9 * 1024 * 1024))
    source.seek(0)
    assert submit(app.test_client(), photo=(source, 'large.png')).status_code == 201


def test_pixel_limit_still_rejects_oversized_images(app, monkeypatch):
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 100)
    source = io.BytesIO()
    Image.new('RGB', (20, 20)).save(source, format='PNG'); source.seek(0)
    result = submit(app.test_client(), photo=(source, 'huge.png'))
    assert result.status_code == 400 and '64 megapixels' in result.json['error']


def test_upgrade_preserves_existing_scores(app):
    c = app.test_client()
    created = submit(c, '254258', initials='TST', game='bubblebobble')
    with sqlite3.connect(str(app.config['DATA_DIR']) + '/arcade.sqlite3') as db:
        before = db.execute('SELECT * FROM scores ORDER BY id').fetchall()
        db.execute('DROP TABLE games')
    reopened = create_app(dict(app.config)).test_client()
    assert len(reopened.get('/api/leaderboard').json['games']) == 33
    with sqlite3.connect(str(app.config['DATA_DIR']) + '/arcade.sqlite3') as db:
        assert db.execute('SELECT * FROM scores ORDER BY id').fetchall() == before
    assert created.status_code == 201


def test_concurrent_new_game_uses_one_catalog_entry(app):
    def post(score):
        return submit(app.test_client(), str(score), game='', gameTitle='Concurrent Cabinet')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(post, [123, 456]))
    assert all(r.status_code == 201 for r in results)
    assert len({r.json['game']['id'] for r in results}) == 1
    assert record(app.test_client(), results[0].json['game']['id'])['score'] == '456'
