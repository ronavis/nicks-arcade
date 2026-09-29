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


def test_account_private_history_and_settings(app):
    c=app.test_client()
    submit(c,'100',token='player')
    submit(c,'200',token='admin')
    assert c.get('/api/account').status_code==401
    assert c.get('/api/activity').status_code==401
    scores=c.get('/api/account',headers=headers()).json['scores']
    assert len(scores)==1 and scores[0]['score']=='100'
    assert 'email' not in scores[0]
    assert c.patch('/api/account',headers=headers(),json={'initials':'nic'}).status_code==200
    assert c.get('/api/account',headers=headers()).json['initials']=='NIC'
    assert c.get('/api/account',headers=headers('admin')).json['initials']==''
    assert c.patch('/api/account',headers=headers(),json={'initials':'ABCD'}).status_code==400
    assert create_app(dict(app.config)).test_client().get('/api/account',headers=headers()).json['initials']=='NIC'


def test_broken_record_notification_taunt_and_read_persistence(app):
    c=app.test_client()
    submit(c,'50000',initials='NIC',token='player')
    submit(c,'51000',initials='RON',token='admin',taunt='Come take the crown!')
    result=c.get('/api/activity',headers=headers()).json
    event=result['events'][0]
    assert event['yourRecordBroken'] and event['isRecord'] and event['unread']
    assert event['score']=='51,000' and event['previousScore']=='50,000' and event['previousInitials']=='NIC'
    assert event['taunt']=='Come take the crown!'
    assert not any(k in event for k in ['user_sub','previous_sub','email'])
    assert c.get('/api/account',headers=headers()).json['unread']==1
    assert c.post('/api/activity/read',headers=headers(),json={'throughId':result['latestId']}).status_code==200
    assert create_app(dict(app.config)).test_client().get('/api/account',headers=headers()).json['unread']==0
    # One player's read cursor never marks another player's feed read.
    assert c.get('/api/account',headers=headers('outsider')).json['unread']==2


def test_no_notification_for_self_record_break_or_equal_score(app):
    c=app.test_client()
    submit(c,'50000',token='player')
    submit(c,'51000',token='player')
    submit(c,'51000',token='admin')
    events=c.get('/api/activity',headers=headers()).json['events']
    assert not any(e['yourRecordBroken'] for e in events)
    assert events[0]['isRecord'] is False
    assert c.get('/api/account',headers=headers()).json['unread']==1


def test_new_game_first_record_and_time_record_notifications(app):
    c=app.test_client()
    first=submit(c,'1:02.30',game='',gameTitle='Notification Racer',gameKind='time')
    game=first.json['game']['id']
    assert c.get('/api/activity',headers=headers('admin')).json['events'][0]['previousScore'] is None
    submit(c,'1:01.00',game=game,token='admin',taunt='Catch me!')
    assert c.get('/api/activity',headers=headers()).json['events'][0]['yourRecordBroken']


def test_activity_idempotency_and_failed_upload_atomicity(app):
    c=app.test_client(); rid=str(uuid.uuid4())
    assert submit(c,requestId=rid,taunt='Hello').status_code==201
    assert submit(c,requestId=rid,taunt='Hello').status_code==200
    assert len(c.get('/api/activity',headers=headers()).json['events'])==1
    assert submit(c,requestId=rid,taunt='Different').status_code==409
    assert submit(c,photo=(io.BytesIO(b'broken'),'broken.heic')).status_code==400
    assert len(c.get('/api/activity',headers=headers()).json['events'])==1


def test_admin_taunt_moderation_and_removed_events(app):
    c=app.test_client()
    result=submit(c,taunt='<img src=x onerror=alert(1)>')
    sid=result.json['record']['id']
    url='/api/admin/scores/'+sid
    payload=dict(score='42500',initials='RON',revision=1,taunt='')
    assert c.patch(url,headers=headers(),json=payload).status_code==403
    assert c.patch(url,headers=headers('admin'),json=payload).status_code==200
    event=c.get('/api/activity',headers=headers()).json['events'][0]
    assert event['taunt']=='' and event['corrected']
    assert c.delete(url,headers=headers('admin'),json={'revision':2}).status_code==200
    assert c.get('/api/activity',headers=headers()).json['events']==[]
    assert c.get('/api/account',headers=headers()).json['scores'][0]['deleted']
    assert c.get('/api/account',headers=headers('outsider')).json['unread']==0


def test_taunt_length_and_read_cursor_validation(app):
    c=app.test_client()
    assert submit(c,taunt='x'*141).status_code==400
    assert submit(c,taunt='x'*140).status_code==201
    for value in [None,-1,True,'1']:
        assert c.post('/api/activity/read',headers=headers(),json={'throughId':value}).status_code==400
    assert c.post('/api/activity/read',json={'throughId':1}).status_code==401
    assert c.post('/api/activity/read',headers=headers(),json={'throughId':999999}).status_code==200
    submit(c,'60000',token='admin')
    assert c.get('/api/account',headers=headers()).json['unread']==1


def test_backup_restores_notifications_and_account_preferences(app,tmp_path):
    from scripts.backup import backup
    c=app.test_client()
    submit(c,'50000',token='player')
    submit(c,'51000',token='admin',taunt='Your turn!')
    c.patch('/api/account',headers=headers(),json={'initials':'NIC'})
    latest=c.get('/api/activity',headers=headers()).json['latestId']
    c.post('/api/activity/read',headers=headers(),json={'throughId':latest})
    # Keep the backup outside the live directory.
    import tempfile
    with tempfile.TemporaryDirectory() as outside:
        destination=backup(app.config['DATA_DIR'],outside+'/snapshot')
        restored=create_app(dict(app.config,DATA_DIR=str(destination))).test_client()
        account=restored.get('/api/account',headers=headers()).json
        assert account['initials']=='NIC' and account['unread']==0
        event=restored.get('/api/activity',headers=headers()).json['events'][0]
        assert event['yourRecordBroken'] and event['taunt']=='Your turn!'


def test_display_timing_shared_and_persistent(app):
    admin,tv=app.test_client(),app.test_client()
    assert tv.get('/api/leaderboard').json['displaySettings']['rotationSeconds']==15
    result=admin.patch('/api/admin/display-settings',headers=headers('admin'),json={'rotationSeconds':8})
    assert result.status_code==200
    assert tv.get('/api/leaderboard').json['displaySettings']['rotationSeconds']==8
    assert admin.get('/api/account',headers=headers('admin')).json['displaySettings']['rotationSeconds']==8
    assert create_app(dict(app.config)).test_client().get('/api/leaderboard').json['displaySettings']['rotationSeconds']==8


def test_display_timing_admin_only_and_validation(app):
    c=app.test_client();url='/api/admin/display-settings'
    assert c.patch(url,json={'rotationSeconds':8}).status_code==401
    assert c.patch(url,headers=headers(),json={'rotationSeconds':8}).status_code==403
    for value in [0,4,121,8.5,'8',True,None]:
        assert c.patch(url,headers=headers('admin'),json={'rotationSeconds':value}).status_code==400
    for value in [5,120]:
        assert c.patch(url,headers=headers('admin'),json={'rotationSeconds':value}).status_code==200


def test_legacy_claim_preserves_records_and_is_durable(tmp_path):
    config = {'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False,
              'TEST_TOKEN_VERIFIER': identity, 'LEGACY_OWNERS': {'RON': 'ronavis@gmail.com', 'RCA': 'ronavis@gmail.com'}}
    app = create_app(config)
    c = app.test_client()
    before = c.get('/api/leaderboard').json['games']
    assert submit(c, initials='RON').status_code == 201
    assert submit(c, initials='TST', token='admin').status_code == 201
    account = c.get('/api/account', headers=headers('admin')).json
    imported = [s for s in account['scores'] if s['createdAt'] is None]
    assert len(imported) == 7 and {s['initials'] for s in imported} == {'RON'}
    assert any(s['initials'] == 'TST' for s in account['scores'])
    assert len(account['scores']) == 8
    # Another player entering RON still owns their own submission.
    own = c.get('/api/account', headers=headers()).json['scores']
    assert len(own) == 1 and own[0]['initials'] == 'RON'
    reopened = create_app(config).test_client()
    assert reopened.get('/api/account', headers=headers('admin')).json['scores'] == account['scores']
    with sqlite3.connect(tmp_path / 'arcade.sqlite3') as db:
        assert db.execute("SELECT count(*) FROM audit WHERE action='link_legacy_account'").fetchone()[0] == 7
        assert db.execute('SELECT count(*) FROM legacy_accounts').fetchone()[0] == 1
    after = c.get('/api/leaderboard').json['games']
    for old, new in zip(before, after):
        if old['id'] != 'galaga':
            assert (old['record']['score'], old['record']['initials']) == (new['record']['score'], new['record']['initials']) if old['record'] else new['record'] is None


def test_legacy_binding_cannot_be_taken_by_different_subject(tmp_path):
    app = create_app({'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False,
                      'TEST_TOKEN_VERIFIER': identity, 'LEGACY_OWNERS': {'NIC': 'player@gmail.com'}})
    c = app.test_client()
    assert len(c.get('/api/account', headers=headers()).json['scores']) == 13
    assert c.get('/api/account', headers=headers('outsider')).json['scores'] == []


@pytest.mark.parametrize('claims', [
    {'sub': 'someone', 'email': 'person@example.com', 'email_verified': True},
    {'sub': 'someone', 'email': 'person@gmail.com', 'email_verified': False},
])
def test_legacy_claim_requires_google_authoritative_verified_email(tmp_path, claims):
    app = create_app({'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False,
                      'TEST_TOKEN_VERIFIER': lambda _: claims, 'LEGACY_OWNERS': {'MAR': claims['email']}})
    app.test_client().get('/api/account', headers=headers())
    with sqlite3.connect(tmp_path / 'arcade.sqlite3') as db:
        assert db.execute("SELECT count(*) FROM scores WHERE user_sub!='imported'").fetchone()[0] == 0


def test_legacy_pending_link_and_removed_record(tmp_path):
    base = {'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False, 'TEST_TOKEN_VERIFIER': identity}
    create_app(base)
    with sqlite3.connect(tmp_path / 'arcade.sqlite3') as db:
        db.execute("UPDATE scores SET deleted_at=123 WHERE initials='MAR'")
    app = create_app(base | {'LEGACY_OWNERS': {'MAR': 'player@gmail.com'}})
    assert app.test_client().get('/api/account', headers=headers('admin')).json['scores'] == []
    rows = app.test_client().get('/api/account', headers=headers()).json['scores']
    assert len(rows) == 3 and all(s['deleted'] and s['initials'] == 'MAR' for s in rows)
    # Removing the mapping does not lose existing ownership.
    assert len(create_app(base).test_client().get('/api/account', headers=headers()).json['scores']) == 3


def test_saved_taunt_settings_persist_and_are_private(app):
    c=app.test_client()
    assert c.get('/api/account',headers=headers()).json['tauntEnabled'] is False
    assert c.patch('/api/account',json={'initials':'ABC'},headers=headers()).status_code==200
    assert c.patch('/api/account',json={'defaultTaunt':'Catch me!', 'tauntEnabled':True},headers=headers()).status_code==200
    account=create_app(dict(app.config)).test_client().get('/api/account',headers=headers()).json
    assert account['initials']=='ABC' and account['defaultTaunt']=='Catch me!' and account['tauntEnabled'] is True
    assert c.get('/api/account',headers=headers('admin')).json['defaultTaunt']==''
    c.patch('/api/account',json={'tauntEnabled':False},headers=headers())
    assert c.get('/api/account',headers=headers()).json['defaultTaunt']=='Catch me!'
    assert c.patch('/api/account',json={'tauntEnabled':'false'},headers=headers()).status_code==400
    assert c.patch('/api/account',json={'defaultTaunt':'a'*141},headers=headers()).status_code==400


def test_automatic_taunt_requires_other_players_record_and_retries(app):
    c=app.test_client()
    c.patch('/api/account',json={'defaultTaunt':'Your turn!', 'tauntEnabled':True},headers=headers())
    for score in ['100','41510']:
        result=submit(c,score,automaticTaunt='true')
        assert result.json['record']['taunt']==''
    rid=str(uuid.uuid4())
    result=submit(c,'50000',automaticTaunt='true',requestId=rid)
    assert result.json['record']['taunt']=='Your turn!'
    c.patch('/api/account',json={'defaultTaunt':'Changed!', 'tauntEnabled':False},headers=headers())
    retry=submit(c,'50000',automaticTaunt='true',requestId=rid)
    assert retry.status_code==200 and retry.json['record']['taunt']=='Your turn!'
    c.patch('/api/account',json={'tauntEnabled':True},headers=headers())
    assert submit(c,'51000',automaticTaunt='true').json['record']['taunt']==''


def test_saved_taunt_disabled_manual_override_and_first_record(app):
    c=app.test_client()
    c.patch('/api/account',json={'defaultTaunt':'Saved', 'tauntEnabled':False},headers=headers())
    assert submit(c,'50000',automaticTaunt='true').json['record']['taunt']==''
    c.patch('/api/account',json={'tauntEnabled':True},headers=headers())
    assert submit(c,'100',game='simpsons',automaticTaunt='true').json['record']['taunt']==''
    assert submit(c,'1:01.00',game='vsexcitebike',automaticTaunt='true').json['record']['taunt']=='Saved'
    assert submit(c,'1:00.00',game='vsexcitebike',taunt='Custom').json['record']['taunt']=='Custom'


def test_public_record_improvement_uses_original_record_break(app):
    c = app.test_client()
    before = c.get('/api/leaderboard').json
    assert all(g['record'] is None or g['record']['improvement'] is None for g in before['games'])
    result = submit(c, '50000').json
    game = next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == 'galaga')
    assert game['record']['improvement']['amount'] == '8,490'
    assert game['record']['improvement']['direction'] == 'up'
    c.patch('/api/admin/scores/' + result['record']['id'], json={'revision': 1, 'score': '51000', 'initials': 'RON'}, headers=headers('admin'))
    game = next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == 'galaga')
    assert game['record']['improvement'] is None


def test_public_record_time_margin_and_non_winner(app):
    c = app.test_client()
    board = c.get('/api/leaderboard').json['games']
    game = next(g for g in board if g['kind'] == 'time')
    # Existing seed is 1:02.30; faster time should use hundredths precisely.
    submit(c, '1:01.20', game=game['id'])
    record = next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == game['id'])['record']
    assert record['improvement']['amount'] == '1.10s'
    assert record['improvement']['direction'] == 'down'
    submit(c, '1:10.00', game=game['id'])
    assert next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == game['id'])['record']['id'] == record['id']


def test_admin_adds_empty_game_without_score_and_deduplicates(app):
    c=app.test_client()
    payload={'title':'  NBA Jam  ', 'kind':'points'}
    assert c.post('/api/admin/games',json=payload).status_code == 401
    assert c.post('/api/admin/games',json=payload,headers=headers()).status_code == 403
    r=c.post('/api/admin/games',json=payload,headers=headers('admin'))
    assert r.status_code == 201
    game_id=r.json['game']['id']
    game=next(g for g in c.get('/api/leaderboard').json['games'] if g['id']==game_id)
    assert game['title']=='NBA Jam' and game['record'] is None
    assert c.get('/api/admin/scores?gameId='+game_id,headers=headers('admin')).json['scores']==[]
    repeat=c.post('/api/admin/games',json={'title':'NBA-Jam','kind':'points'},headers=headers('admin'))
    assert repeat.status_code==200 and repeat.json['alreadyExists']
    assert repeat.json['game']['id']==game_id
    assert c.post('/api/admin/games',json={'title':'NBA Jam','kind':'time'},headers=headers('admin')).status_code==400
    assert submit(c,'200',game=game_id).status_code==201
    assert next(g for g in c.get('/api/leaderboard').json['games'] if g['id']==game_id)['record']['score']=='200'


def test_admin_add_game_validates_title_and_type(app):
    c=app.test_client()
    for payload in [None,[],{'title':''},{'title':'x'},{'title':'x'*81},{'title':'Good Game','kind':'invalid'}]:
        assert c.post('/api/admin/games',json=payload,headers=headers('admin')).status_code==400
    r=c.post('/api/admin/games',json={'title':'Fast Racer','kind':'time'},headers=headers('admin'))
    assert r.status_code==201
    assert submit(c,'1:02.30',game=r.json['game']['id']).status_code==201
