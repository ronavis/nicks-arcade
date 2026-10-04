import uuid

import pytest

from server.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({'TESTING': True, 'DATA_DIR': str(tmp_path), 'DEMO': False,
                      'TEST_TOKEN_VERIFIER': lambda token: {'sub': token, 'email': token+'@example.invalid', 'email_verified': True}})
    return app.test_client()


def auth(user):
    return {'Authorization': 'Bearer '+user, 'Origin': 'https://ronavis.github.io'}


def run(client, user, score):
    result = client.post('/api/movie-ladder/runs', headers=auth(user), json={
        'id': str(uuid.uuid4()), 'score': score, 'rungReached': 10, 'completed': True,
        'livesRemaining': 3, 'correctCount': 10, 'wrongCount': 0, 'maxStreak': 10,
    })
    assert result.status_code == 201


def profile(client, user, name, sharing=True):
    return client.put('/api/movie-ladder/leaderboard-profile', headers=auth(user), json={'displayName': name, 'sharing': sharing})


def test_private_until_opt_in_and_withdrawal(client):
    run(client, 'one', 5000)
    assert client.get('/api/movie-ladder/leaderboard').json == {'leaders': []}
    assert client.get('/api/movie-ladder/leaderboard-profile', headers=auth('one')).json == {'displayName': '', 'sharing': False}
    assert profile(client, 'one', 'Reel Fan').status_code == 200
    public = client.get('/api/movie-ladder/leaderboard')
    assert public.headers['Cache-Control'] == 'no-store'
    assert public.json['leaders'] == [{'position': 1, 'name': 'Reel Fan', 'score': 5000, 'rungReached': 10, 'completed': True, 'rank': 'Cinemaster'}]
    assert profile(client, 'one', 'Reel Fan', False).status_code == 200
    assert client.get('/api/movie-ladder/leaderboard').json == {'leaders': []}
    assert client.get('/api/movie-ladder/runs', headers=auth('one')).json['summary']['totalRuns'] == 1


def test_one_best_per_player_order_limits_and_isolation(client):
    for user, score in [('one', 5000), ('one', 5100), ('two', 5500), ('private', 6000)]:
        run(client, user, score)
    profile(client, 'one', 'Player One')
    profile(client, 'two', 'Player Two')
    leaders = client.get('/api/movie-ladder/leaderboard').json['leaders']
    assert [row['score'] for row in leaders] == [5500, 5100]
    assert [row['position'] for row in leaders] == [1, 2]
    assert len(client.get('/api/movie-ladder/leaderboard?limit=1').json['leaders']) == 1
    assert client.get('/api/movie-ladder/leaderboard-profile', headers=auth('private')).json['sharing'] is False
    assert '@' not in str(leaders) and 'user_sub' not in str(leaders) and 'user_email' not in str(leaders)
    assert profile(client, 'one', 'Changed Name').status_code == 200
    assert client.get('/api/movie-ladder/leaderboard-profile', headers=auth('two')).json['displayName'] == 'Player Two'


@pytest.mark.parametrize('limit', ['0', '11', '-1', '1.0', 'x', '100000'])
def test_invalid_limit(client, limit):
    assert client.get('/api/movie-ladder/leaderboard?limit='+limit).status_code == 400


@pytest.mark.parametrize('name', ['', 'X', 'a@example.com', '<script>', '=SUM(1)', 'X'*25, '🙂🙂', 123])
def test_invalid_public_names(client, name):
    assert profile(client, 'one', name).status_code == 400


def test_profile_authentication_and_boolean_validation(client):
    assert client.get('/api/movie-ladder/leaderboard-profile').status_code == 401
    assert client.put('/api/movie-ladder/leaderboard-profile', json={'displayName': 'Test', 'sharing': True}).status_code == 401
    assert client.put('/api/movie-ladder/leaderboard-profile', headers=auth('one'), json={'displayName': 'Test', 'sharing': 'true'}).status_code == 400
    assert profile(client, 'one', 'Écho').status_code == 200
