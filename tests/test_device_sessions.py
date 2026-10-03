import hashlib
import sqlite3
import time
import io
from PIL import Image
from test_api import app,headers
from server.app import create_app


def test_remembered_session_expiry_hashing_restart_and_logout(app):
    c=app.test_client()
    assert c.post('/api/session',json={'remember':True}).status_code==401
    assert c.post('/api/session',json={'remember':True},headers=headers('unverified')).status_code==401
    r=c.post('/api/session',json={'remember':True},headers=headers('admin'))
    assert r.status_code==200 and r.headers['Cache-Control']=='no-store'
    token=r.json['token'];assert token.startswith('arcade_')
    assert abs(r.json['expiresAt']-time.time()-30*86400)<5
    with sqlite3.connect(str(app.config['DATA_DIR'])+'/arcade.sqlite3') as db:
        row=db.execute('SELECT token_hash,identity_json FROM arcade_sessions').fetchone()
        assert row[0]==hashlib.sha256(token.encode()).hexdigest() and token not in str(row)
    c=create_app(dict(app.config)).test_client()
    assert c.get('/api/session',headers=headers(token)).json['admin'] is True
    assert c.post('/api/session',json={'remember':True},headers=headers(token)).status_code==400
    assert c.delete('/api/session',headers=headers(token)).status_code==200
    assert c.get('/api/session',headers=headers(token)).status_code==401


def test_short_session_expiration_and_current_admin_permissions(app):
    c=app.test_client()
    token=c.post('/api/session',json={'remember':False},headers=headers('admin')).json['token']
    app.config['ADMIN_EMAILS']=set()
    assert c.get('/api/session',headers=headers(token)).json['admin'] is False
    assert c.get('/api/admin/cabinets',headers=headers(token)).status_code==403
    with sqlite3.connect(str(app.config['DATA_DIR'])+'/arcade.sqlite3') as db:
        expiry=db.execute('SELECT expires_at FROM arcade_sessions').fetchone()[0]
        assert abs(expiry-time.time()-86400)<5
        db.execute('UPDATE arcade_sessions SET expires_at=0')
    assert c.get('/api/session',headers=headers(token)).status_code==401


def test_player_sessions_cannot_admin_and_public_photo_caching(app):
    c=app.test_client();token=c.post('/api/session',json={'remember':True},headers=headers()).json['token']
    assert c.get('/api/admin/cabinets',headers=headers(token)).status_code==403
    im=io.BytesIO();Image.new('RGB',(20,20),'blue').save(im,'PNG');im.seek(0)
    r=c.post('/api/admin/cabinets/nick-pac/photo',data={'revision':'1','photo':(im,'test.png')},headers=headers('admin'))
    pid=next(row['photoId'] for row in r.json['cabinets'] if row['id']=='nick-pac')
    assert 'immutable' in c.get('/api/cabinet-photos/'+pid).headers['Cache-Control']
    assert c.get('/api/cabinet-photos/missing').headers['Cache-Control']=='no-store'
    assert c.get('/api/leaderboard').headers['Cache-Control']=='no-store'
