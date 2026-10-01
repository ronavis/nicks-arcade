from test_api import app, headers, submit
from server.app import create_app


def test_visibility_defaults_permissions_and_persistence(app):
    c = app.test_client()
    games = c.get('/api/leaderboard').json['games']
    assert all(g['showOnLeaderboard'] == bool(g['record']) for g in games)
    empty = next(g for g in games if not g['record'] and g['eligible'])
    url = '/api/admin/games/' + empty['id'] + '/leaderboard'
    assert c.patch(url, json={'showOnLeaderboard': True}).status_code == 401
    assert c.patch(url, json={'showOnLeaderboard': True}, headers=headers()).status_code == 403
    assert c.patch(url, json={'showOnLeaderboard': 'yes'}, headers=headers('admin')).status_code == 400
    assert c.patch(url, json={'showOnLeaderboard': True}, headers=headers('admin')).status_code == 200
    c = create_app(dict(app.config)).test_client()
    assert next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == empty['id'])['showOnLeaderboard'] == 1
    assert c.patch(url, json={'showOnLeaderboard': False}, headers=headers('admin')).status_code == 200
    assert submit(c, game=empty['id']).status_code == 201
    c = create_app(dict(app.config)).test_client()
    game = next(g for g in c.get('/api/leaderboard').json['games'] if g['id'] == empty['id'])
    assert game['record'] and game['eligible'] and game['showOnLeaderboard'] == 0
    new = c.post('/api/admin/games', json={'title':'Visibility Test Game','kind':'points'}, headers=headers('admin'))
    assert new.status_code in (200,201)
    assert next(g for g in c.get('/api/leaderboard').json['games'] if g['title']=='Visibility Test Game')['showOnLeaderboard'] == 0
