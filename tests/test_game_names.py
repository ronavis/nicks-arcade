import sqlite3
from test_api import app, headers
from server.app import create_app


def test_rename_roles_conflicts_and_preservation(app):
    c=app.test_client();url='/api/admin/games/galaga/name'
    body={'title':'Galaga Deluxe','expectedTitle':'Galaga'}
    assert c.patch(url,json=body).status_code==401
    assert c.patch(url,json=body,headers=headers()).status_code==403
    assert c.patch(url,json={**body,'title':' '},headers=headers('admin')).status_code==400
    assert c.patch(url,json={**body,'title':'Pac-Man'},headers=headers('admin')).status_code==409
    assert c.patch(url,json={**body,'expectedTitle':'old'},headers=headers('admin')).status_code==409
    dbpath=str(app.config['DATA_DIR'])+'/arcade.sqlite3'
    with sqlite3.connect(dbpath) as db:
        scores=db.execute('SELECT * FROM scores ORDER BY id').fetchall()
        links=db.execute('SELECT * FROM cabinet_games ORDER BY 1,2').fetchall()
    assert c.patch(url,json=body,headers=headers('admin')).status_code==200
    c=create_app(dict(app.config)).test_client()
    game=next(g for g in c.get('/api/leaderboard').json['games'] if g['id']=='galaga')
    assert game['title']=='Galaga Deluxe' and game['record']['score']=='41,510'
    with sqlite3.connect(dbpath) as db:
        assert db.execute('SELECT * FROM scores ORDER BY id').fetchall()==scores
        assert db.execute('SELECT * FROM cabinet_games ORDER BY 1,2').fetchall()==links


def test_old_custom_name_can_be_added_after_rename(app):
    c=app.test_client();h=headers('admin')
    first=c.post('/api/admin/games',json={'title':'Original Test','kind':'points'},headers=h).json['game']
    assert c.patch('/api/admin/games/'+first['id']+'/name',json={'title':'Renamed Test','expectedTitle':'Original Test'},headers=h).status_code==200
    second=c.post('/api/admin/games',json={'title':'Original Test','kind':'points'},headers=h)
    assert second.status_code==201 and second.json['game']['id']!=first['id']
