import sqlite3
from test_api import app, headers


def call(c, csv, mode='preview', token='admin', **kw):
    return c.post('/api/admin/inventory-import',json=dict(csv=csv,mode=mode,**kw),headers=headers(token))


def test_preview_commit_repeat_and_preservation(app):
    c=app.test_client()
    source='Game,Cabinet 1,Cabinet 2,Scoring\nGalaga,New Cabinet,Second Cabinet,points\nGalaga,New Cabinet,,\nNew Time Game,Second Cabinet,,time\nUnassigned Game,,,\n'
    with sqlite3.connect(str(app.config['DATA_DIR'])+'/arcade.sqlite3') as db:
        before=db.execute('SELECT * FROM scores ORDER BY id').fetchall()
        db.execute("UPDATE games SET eligible=0,marquee_id='original' WHERE id='galaga'")
    result=call(c,source).json
    assert result['counts']==dict(games=2,cabinets=2,assignments=3)
    assert not result['errors'] and result['rows'][0]['eligible']==0
    assert len(c.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])==18
    assert call(c,source,'commit',previewHash=result['previewHash']).status_code==200
    assert call(c,source).json['counts']==dict(games=0,cabinets=0,assignments=0)
    with sqlite3.connect(str(app.config['DATA_DIR'])+'/arcade.sqlite3') as db:
        assert db.execute('SELECT * FROM scores ORDER BY id').fetchall()==before
        assert db.execute("SELECT eligible,marquee_id FROM games WHERE id='galaga'").fetchone()==(0,'original')
        assert db.execute("SELECT COUNT(*) FROM cabinet_games WHERE game_id='galaga'").fetchone()[0]==5
        assert db.execute("SELECT COUNT(*) FROM cabinet_audit WHERE action='import'").fetchone()[0]==1


def test_invalid_rows_atomicity_and_roles(app):
    c=app.test_client()
    assert call(c,'Game\nHello','preview','player').status_code==403
    assert c.post('/api/admin/inventory-import',json={}).status_code==401
    for source in ['Game,Score\nGalaga,100','Game,Game\nA,B','Game\n','x'*262145,'Game\n'+('Valid Game\n'*501),'Game,Cabinet 1\n"unclosed,word']:
        assert call(c,source).status_code==400
    source='Game,Cabinet 1,Scoring\nValid New Game,New Cabinet,points\nGalaga,New Cabinet,time\n=BAD(),,points\n'
    p=call(c,source).json
    assert len(p['errors'])==2
    assert call(c,source,'commit',previewHash=p['previewHash']).status_code==400
    assert len(c.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])==18


def test_stale_preview_and_unicode_csv(app):
    c=app.test_client();source='\ufeffGame,Cabinet 1\r\n"New, Game","Ron’s Cabinet"\r\n'
    p=call(c,source).json
    assert not p['errors']
    c.post('/api/admin/cabinets',json={'name':'Ron’s Cabinet'},headers=headers('admin'))
    assert call(c,source,'commit',previewHash=p['previewHash']).status_code==409
    p=call(c,source).json
    assert call(c,source,'commit',previewHash=p['previewHash']).status_code==200
    assert call(c,source).json['counts']==dict(games=0,cabinets=0,assignments=0)
