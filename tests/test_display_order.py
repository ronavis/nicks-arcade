from test_api import app, headers
from server.app import create_app


def test_shared_order_authorization_validation_and_restart(app):
    c = app.test_client()
    path = '/api/admin/display-settings'
    assert c.get('/api/leaderboard').json['displaySettings']['leaderboardOrder'] == 'alphabetical'
    assert c.patch(path, json={'leaderboardOrder':'newest'}).status_code == 401
    assert c.patch(path, json={'leaderboardOrder':'newest'}, headers=headers()).status_code == 403
    for invalid in ['random', None, [], {}, 1]:
        assert c.patch(path, json={'leaderboardOrder':invalid}, headers=headers('admin')).status_code == 400
    assert c.patch(path, json={'leaderboardOrder':'newest'}, headers=headers('admin')).status_code == 200
    c = create_app(dict(app.config)).test_client()
    assert c.get('/api/leaderboard').json['displaySettings']['leaderboardOrder'] == 'newest'
    assert c.get('/api/account', headers=headers('admin')).json['displaySettings']['leaderboardOrder'] == 'newest'
    assert c.patch(path, json={'rotationSeconds':10}, headers=headers('admin')).json['displaySettings']['leaderboardOrder'] == 'newest'
    assert c.patch(path, json={'leaderboardOrder':'alphabetical'}, headers=headers('admin')).json['displaySettings']['leaderboardOrder'] == 'alphabetical'
