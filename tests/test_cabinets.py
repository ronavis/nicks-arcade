import io
import sqlite3
from PIL import Image
from test_api import app, headers, record
from server.app import create_app
from scripts.backup import backup


def test_complete_inventory_and_upgrade_preserves_admin_choices(app):
    c = app.test_client()
    games = c.get('/api/leaderboard').json['games']
    by_title = {g['title']: g for g in games}
    rows = c.get('/api/admin/cabinets', headers=headers('admin')).json['cabinets']
    dragon = next(r for r in rows if r['id'] == 'nick-drl')
    assert set(dragon['gameIds']) == {by_title[t]['id'] for t in ["Dragon's Lair", "Dragon's Lair II: Time Warp", 'Space Ace']}
    assert by_title['Space Ace']['record'] is None
    assert by_title["Dragon's Lair II: Time Warp"]['record'] is None
    assert next(r for r in rows if r['id'] == 'nick-dkj')['gameIds'] == ['donkeykongjunior']
    assert 'Donkey Kong Jr.' not in by_title
    assert 'Street Fighter II' not in by_title
    assert 'Tekken 4' not in by_title
    assert all(r['code'] != 'MC2' for r in rows)
    # Simulate upgrading the earlier cabinets-only release with edited links.
    c.put('/api/admin/games/galaga/cabinets', json={'expectedCabinetIds':['nick-pac','nick-pcm','nick-ckt'],'cabinetIds':[]}, headers=headers('admin'))
    with sqlite3.connect(str(app.config['DATA_DIR']) + '/arcade.sqlite3') as db:
        before = db.execute('SELECT * FROM scores ORDER BY id').fetchall()
        db.execute("DELETE FROM metadata WHERE key='cabinet_games_v2'")
        db.execute("UPDATE games SET eligible=0,marquee_id='keep-custom' WHERE id='dragonslair'")
        gid = by_title['Space Ace']['id']
        db.execute('DELETE FROM cabinet_games WHERE game_id=?', (gid,))
        db.execute('DELETE FROM games WHERE id=?', (gid,))
    reopened = create_app(dict(app.config)).test_client()
    rows = reopened.get('/api/admin/cabinets', headers=headers('admin')).json['cabinets']
    assert all('galaga' not in r['gameIds'] for r in rows)
    assert gid in next(r for r in rows if r['id']=='nick-drl')['gameIds']
    with sqlite3.connect(str(app.config['DATA_DIR']) + '/arcade.sqlite3') as db:
        assert db.execute('SELECT * FROM scores ORDER BY id').fetchall() == before
        assert db.execute("SELECT eligible,marquee_id FROM games WHERE id='dragonslair'").fetchone() == (0,'keep-custom')


def test_seed_is_one_time_and_preserves_scores(app):
    c=app.test_client()
    before=record(c)
    rows=c.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets']
    assert len(rows)==19
    assert sum('galaga' in r['gameIds'] for r in rows)==3
    r=c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':['nick-pac','nick-pcm','nick-ckt'],'cabinetIds':[]},headers=headers('admin'))
    assert r.status_code==200
    reopened=create_app(dict(app.config)).test_client()
    assert all('galaga' not in r['gameIds'] for r in reopened.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])
    assert record(reopened)==before


def test_roles_validation_and_stale_assignments(app):
    c=app.test_client()
    assert c.get('/api/admin/cabinets').status_code==401
    assert c.get('/api/admin/cabinets',headers=headers()).status_code==403
    assert c.post('/api/admin/cabinets',json={'name':'test'},headers=headers()).status_code==403
    assert c.put('/api/admin/games/galaga/cabinets',json={},headers=headers()).status_code==403
    assert c.post('/api/admin/cabinets/nick-pac/photo',headers=headers()).status_code==403
    assert c.post('/api/admin/cabinets',json={'name':' '},headers=headers('admin')).status_code==400
    result=c.post('/api/admin/cabinets',json={'name':'Test cabinet'},headers=headers('admin')).json
    cid=result['id']
    assert c.post('/api/admin/cabinets',json={'name':'TEST CABINET'},headers=headers('admin')).status_code==409
    assert c.patch('/api/admin/cabinets/'+cid,json={'name':'Renamed','revision':0},headers=headers('admin')).status_code==409
    assert c.patch('/api/admin/cabinets/'+cid,json={'name':'Renamed','revision':1},headers=headers('admin')).status_code==200
    old=['nick-pac','nick-pcm','nick-ckt']
    assert c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':old,'cabinetIds':old+[cid]},headers=headers('admin')).status_code==200
    assert c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':old,'cabinetIds':[]},headers=headers('admin')).status_code==409
    assert c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':old+[cid],'cabinetIds':['missing']},headers=headers('admin')).status_code==400
    assert record(c)['score']=='41,510'


def test_photo_and_backup(app,tmp_path):
    c=app.test_client()
    def photo(revision):
        f=io.BytesIO();Image.new('RGB',(100,200),'red').save(f,format='PNG');f.seek(0)
        return c.post('/api/admin/cabinets/nick-pac/photo',data={'revision':str(revision),'photo':(f,'cabinet.png')},headers=headers('admin'))
    result=photo(1);assert result.status_code==200
    pid=next(r['photoId'] for r in result.json['cabinets'] if r['id']=='nick-pac')
    assert c.get('/api/cabinet-photos/'+pid).status_code==200
    assert photo(1).status_code==409
    assert len(list((tmp_path/'cabinets').glob('*.jpg')))==1
    destination=tmp_path.parent/(tmp_path.name+'-backup')
    backup(tmp_path,destination)
    assert (destination/'cabinets'/f'{pid}.jpg').exists()
    restored=create_app(dict(app.config,DATA_DIR=str(destination))).test_client()
    assert restored.get('/api/cabinet-photos/'+pid).status_code==200
    assert len(restored.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])==19


def test_pages_preflight_allows_assignments(app):
    r=app.test_client().options('/api/admin/games/galaga/cabinets',headers={'Origin':'https://ronavis.github.io','Access-Control-Request-Method':'PUT','Access-Control-Request-Headers':'authorization,content-type'})
    assert r.status_code==204
    assert 'PUT' in r.headers['Access-Control-Allow-Methods']


def test_public_board_exposes_only_cabinet_display_fields(app):
    c=app.test_client()
    def assigned():
        return next(g for g in c.get('/api/leaderboard').json['games'] if g['id']=='galaga')['cabinets']
    rows=assigned()
    assert {r['id'] for r in rows}=={'nick-pac','nick-pcm','nick-ckt'}
    assert all(set(r)=={'id','name','code','photoId'} for r in rows)
    image=io.BytesIO();Image.new('RGB',(80,120),'blue').save(image,format='PNG');image.seek(0)
    assert c.post('/api/admin/cabinets/nick-pac/photo',data={'revision':'1','photo':(image,'photo.png')},headers=headers('admin')).status_code==200
    photo=next(r for r in assigned() if r['id']=='nick-pac')['photoId']
    assert photo and c.get('/api/cabinet-photos/'+photo).status_code==200
    assert c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':[r['id'] for r in rows],'cabinetIds':[]},headers=headers('admin')).status_code==200
    assert assigned()==[]


def test_reference_images_cover_seeded_cabinets():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    art=json.loads((root/'data/cabinet-art.json').read_text())
    seed=json.loads((root/'data/cabinets.json').read_text())
    assert set(art)=={c['code'] for c in seed}
    for reference in art.values():
        with Image.open(root/reference['image']) as im:
            im.verify()
        assert reference['source'].startswith('https://')


def test_remove_cabinet_roles_conflicts_preservation_and_restart(app):
    import json
    c=app.test_client()
    cid=c.post('/api/admin/cabinets',json={'name':'Accidental cabinet'},headers=headers('admin')).json['id']
    body={'revision':1,'expectedGameIds':[]}
    assert c.delete('/api/admin/cabinets/'+cid,json=body).status_code==401
    assert c.delete('/api/admin/cabinets/'+cid,json=body,headers=headers()).status_code==403
    assert c.delete('/api/admin/cabinets/'+cid,json={**body,'revision':0},headers=headers('admin')).status_code==409
    assert c.delete('/api/admin/cabinets/'+cid,json={'revision':1},headers=headers('admin')).status_code==400
    old=['nick-pac','nick-pcm','nick-ckt']
    c.put('/api/admin/games/galaga/cabinets',json={'expectedCabinetIds':old,'cabinetIds':old+[cid]},headers=headers('admin'))
    assert c.delete('/api/admin/cabinets/'+cid,json=body,headers=headers('admin')).status_code==409
    dbpath=str(app.config['DATA_DIR'])+'/arcade.sqlite3'
    with sqlite3.connect(dbpath) as db:
        games=db.execute('SELECT * FROM games ORDER BY id').fetchall()
        scores=db.execute('SELECT * FROM scores ORDER BY id').fetchall()
    result=c.delete('/api/admin/cabinets/'+cid,json={'revision':1,'expectedGameIds':['galaga']},headers=headers('admin'))
    assert result.status_code==200
    assert all(r['id']!=cid for r in result.json['cabinets'])
    with sqlite3.connect(dbpath) as db:
        assert db.execute('SELECT * FROM games ORDER BY id').fetchall()==games
        assert db.execute('SELECT * FROM scores ORDER BY id').fetchall()==scores
        assert {r[0] for r in db.execute("SELECT cabinet_id FROM cabinet_games WHERE game_id='galaga'")}==set(old)
        audit=json.loads(db.execute("SELECT before_json FROM cabinet_audit WHERE action='remove'").fetchone()[0])
        assert audit['gameIds']==['galaga'] and audit['name']=='Accidental cabinet'
    reopened=create_app(dict(app.config)).test_client()
    assert all(r['id']!=cid for r in reopened.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])
    assert c.delete('/api/admin/cabinets/'+cid,json=body,headers=headers('admin')).status_code==404


def test_remove_empty_cabinet(app):
    c=app.test_client()
    cid=c.post('/api/admin/cabinets',json={'name':'Empty mistake'},headers=headers('admin')).json['id']
    assert c.delete('/api/admin/cabinets/'+cid,json={'revision':1,'expectedGameIds':[]},headers=headers('admin')).status_code==200
