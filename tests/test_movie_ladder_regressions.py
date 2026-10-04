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
    if token not in {'player', 'admin', 'nick', 'unverified', 'outsider'}:
        raise ValueError('Invalid test identity')
    email = {'admin': 'ronavis@gmail.com', 'nick': 'nick@gmail.com'}.get(token, 'player@gmail.com')
    return {'sub': token, 'email': email, 'email_verified': token != 'unverified'}


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


def marquee_upload(c, game='galaga', token='admin', expected='', image=None):
    if image is None:
        image = io.BytesIO()
        original = Image.new('RGBA', (2400, 600), (255, 0, 0, 100))
        exif = Image.Exif(); exif[315] = 'private metadata'
        original.save(image, format='PNG', exif=exif)
        image.seek(0)
    return c.post('/api/admin/games/' + game + '/marquee', data={'marquee':(image,'image.png'), 'expectedMarqueeId':expected}, headers=headers(token))


class FakeTmdbResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


def test_movie_ladder_tmdb_is_ron_only_even_for_another_arcade_admin(app, monkeypatch):
    app.config['ADMIN_EMAILS'].add('nick@gmail.com')
    c = app.test_client()
    assert c.get('/api/session', headers=headers('nick')).json['admin'] is True
    assert c.get('/api/movie-ladder/admin/tmdb', headers=headers('nick')).status_code == 403
    assert c.get('/api/movie-ladder/admin/tmdb', headers=headers('admin')).json == {
        'configured': False, 'lastVerifiedAt': None
    }

    calls = []
    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append((url, headers, params, timeout))
        return FakeTmdbResponse({'images': {}})

    import server.app as module
    monkeypatch.setattr(module.requests, 'get', fake_get)
    token = 'tmdb-read-token-' + ('x' * 40)
    saved = c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token})
    assert saved.status_code == 200
    assert saved.json['configured'] is True
    assert token not in saved.text
    status = c.get('/api/movie-ladder/admin/tmdb', headers=headers('admin'))
    assert status.status_code == 200 and status.json['configured'] is True
    assert token not in status.text
    assert calls[0][0].endswith('/configuration')
    assert calls[0][1]['Authorization'] == 'Bearer ' + token
    assert calls[0][3] == 10


def test_movie_ladder_tmdb_rejected_token_is_not_saved(app, monkeypatch):
    import server.app as module
    monkeypatch.setattr(
        module.requests,
        'get',
        lambda *a, **k: FakeTmdbResponse({'status_message': 'Invalid API key'}, 401),
    )
    c = app.test_client()
    token = 'tmdb-read-token-' + ('y' * 40)
    response = c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token})
    assert response.status_code == 502
    status = c.get('/api/movie-ladder/admin/tmdb', headers=headers('admin'))
    assert status.json == {'configured': False, 'lastVerifiedAt': None}


def test_movie_ladder_tmdb_search_uses_private_stored_token_and_normalizes_artwork(app, monkeypatch):
    import server.app as module
    requests_seen = []

    def fake_get(url, headers=None, params=None, timeout=None):
        requests_seen.append((url, dict(headers or {}), dict(params or {})))
        if url.endswith('/configuration'):
            return FakeTmdbResponse({'images': {}})
        if url.endswith('/search/movie'):
            return FakeTmdbResponse({'results': [{
                'id': 578,
                'title': 'Jaws',
                'release_date': '1975-06-20',
                'poster_path': '/poster.jpg',
                'backdrop_path': '/backdrop.jpg',
            }]})
        raise AssertionError(url)

    monkeypatch.setattr(module.requests, 'get', fake_get)
    c = app.test_client()
    token = 'tmdb-read-token-' + ('z' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200

    result = c.get('/api/movie-ladder/tmdb/search?title=Jaws&year=1975')
    assert result.status_code == 200
    assert result.json == {
        'id': 578,
        'title': 'Jaws',
        'releaseDate': '1975-06-20',
        'poster': 'https://image.tmdb.org/t/p/w500/poster.jpg',
        'backdrop': 'https://image.tmdb.org/t/p/w780/backdrop.jpg',
    }
    assert token not in result.text
    search = requests_seen[-1]
    assert search[1]['Authorization'] == 'Bearer ' + token
    assert search[2]['query'] == 'Jaws'
    assert search[2]['year'] == '1975'


def test_movie_ladder_tmdb_test_and_disconnect(app, monkeypatch):
    import server.app as module
    monkeypatch.setattr(module.requests, 'get', lambda *a, **k: FakeTmdbResponse({'images': {}}))
    c = app.test_client()
    token = 'tmdb-read-token-' + ('q' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200
    tested = c.post('/api/movie-ladder/admin/tmdb/test', headers=headers('admin'))
    assert tested.status_code == 200 and tested.json['ok'] is True
    removed = c.delete('/api/movie-ladder/admin/tmdb', headers=headers('admin'))
    assert removed.json == {'configured': False}
    assert c.get('/api/movie-ladder/tmdb/search?title=Jaws&year=1975').status_code == 503


def test_movie_ladder_tmdb_person_prefers_actor_and_returns_profile(app, monkeypatch):
    import server.app as module

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith('/configuration'):
            return FakeTmdbResponse({'images': {}})
        if url.endswith('/search/person'):
            assert params['query'] == 'Harrison Ford'
            return FakeTmdbResponse({'results': [
                {
                    'id': 999,
                    'name': 'Harrison Ford',
                    'known_for_department': 'Directing',
                    'profile_path': '/wrong.jpg',
                },
                {
                    'id': 3,
                    'name': 'Harrison Ford',
                    'known_for_department': 'Acting',
                    'profile_path': '/harrison.jpg',
                },
            ]})
        raise AssertionError(url)

    monkeypatch.setattr(module.requests, 'get', fake_get)
    c = app.test_client()
    token = 'tmdb-read-token-' + ('p' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200

    result = c.get('/api/movie-ladder/tmdb/person?name=Harrison%20Ford')
    assert result.status_code == 200
    assert result.json == {
        'id': 3,
        'name': 'Harrison Ford',
        'department': 'Acting',
        'profile': 'https://image.tmdb.org/t/p/w185/harrison.jpg',
    }
    assert token not in result.text


def test_movie_ladder_tmdb_person_missing_profile_is_safe(app, monkeypatch):
    import server.app as module

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith('/configuration'):
            return FakeTmdbResponse({'images': {}})
        if url.endswith('/search/person'):
            return FakeTmdbResponse({'results': [{
                'id': 4,
                'name': 'No Photo Actor',
                'known_for_department': 'Acting',
                'profile_path': None,
            }]})
        raise AssertionError(url)

    monkeypatch.setattr(module.requests, 'get', fake_get)
    c = app.test_client()
    token = 'tmdb-read-token-' + ('r' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200
    result = c.get('/api/movie-ladder/tmdb/person?name=No%20Photo%20Actor')
    assert result.status_code == 200
    assert result.json['profile'] is None


def test_movie_ladder_tmdb_person_can_prefer_director_department(app, monkeypatch):
    import server.app as module

    def fake_get(url, headers=None, params=None, timeout=None):
        if url.endswith('/configuration'):
            return FakeTmdbResponse({'images': {}})
        if url.endswith('/search/person'):
            assert params['query'] == 'John Carpenter'
            return FakeTmdbResponse({'results': [
                {
                    'id': 100,
                    'name': 'John Carpenter',
                    'known_for_department': 'Acting',
                    'profile_path': '/actor.jpg',
                },
                {
                    'id': 11770,
                    'name': 'John Carpenter',
                    'known_for_department': 'Directing',
                    'profile_path': '/director.jpg',
                },
            ]})
        raise AssertionError(url)

    monkeypatch.setattr(module.requests, 'get', fake_get)
    c = app.test_client()
    token = 'tmdb-read-token-' + ('d' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200

    result = c.get('/api/movie-ladder/tmdb/person?name=John%20Carpenter&department=Directing')
    assert result.status_code == 200
    assert result.json == {
        'id': 11770,
        'name': 'John Carpenter',
        'department': 'Directing',
        'profile': 'https://image.tmdb.org/t/p/w185/director.jpg',
    }


def test_movie_ladder_tmdb_person_rejects_unknown_department(app, monkeypatch):
    import server.app as module
    monkeypatch.setattr(module.requests, 'get', lambda *a, **k: FakeTmdbResponse({'images': {}}))
    c = app.test_client()
    token = 'tmdb-read-token-' + ('e' * 40)
    assert c.put('/api/movie-ladder/admin/tmdb', headers=headers('admin'), json={'token': token}).status_code == 200
    assert c.get('/api/movie-ladder/tmdb/person?name=Someone&department=Producing').status_code == 400


MOVIE_LADDER_CSV = """rung,question,answer_type,answer1,answer1_year,answer2,answer2_year,answer3,answer3_year,answer4,answer4_year,correct,explanation,display_title,display_year,genre,hero_movie,hero_year,difficulty,points
1,Who played Indiana Jones?,actor,Harrison Ford,,Kurt Russell,,Tom Selleck,,Michael Douglas,,1,Harrison Ford played Indiana Jones.,Raiders of the Lost Ark,1981,Adventure,Raiders of the Lost Ark,1981,Warm-up,100
2,Who directed Jaws?,director,George Lucas,,Steven Spielberg,,Brian De Palma,,William Friedkin,,2,Steven Spielberg directed Jaws.,Jaws,1975,Thriller,Jaws,1975,Warm-up,200
5,Which movie was released first?,movie,Rocky,1976,Star Wars,1977,Jaws,1975,Alien,1979,3,Jaws was released in 1975.,Release Order,,Timeline,,,Movie buff,500
10,Which juror votes not guilty first?,text,Juror 3,,Juror 8,,Juror 9,,Juror 12,,2,Juror 8 casts the first not-guilty vote.,12 Angry Men,1957,Drama,12 Angry Men,1957,Cinemaster,1000
"""


def test_movie_ladder_question_bank_starts_empty_and_public(app):
    c = app.test_client()
    result = c.get('/api/movie-ladder/questions')
    assert result.status_code == 200
    assert result.json == {'questions': [], 'count': 0}


def test_movie_ladder_csv_validation_is_admin_only_and_non_mutating(app):
    c = app.test_client()
    payload = {'csv': MOVIE_LADDER_CSV}

    assert c.post('/api/movie-ladder/admin/questions/validate', json=payload).status_code == 401
    assert c.post('/api/movie-ladder/admin/questions/validate', headers=headers(), json=payload).status_code == 403
    assert c.post('/api/movie-ladder/admin/questions/validate', headers=headers('nick'), json=payload).status_code == 403

    result = c.post('/api/movie-ladder/admin/questions/validate', headers=headers('admin'), json=payload)
    assert result.status_code == 200
    assert result.json['valid'] is True
    assert result.json['count'] == 4
    assert result.json['truncated'] is False
    preview = result.json['preview']

    actor = preview[0]
    assert actor['rung'] == 1
    assert actor['correct'] == 0
    assert actor['personDepartment'] == 'Acting'
    assert actor['answerPeople'] == [['Harrison Ford'], ['Kurt Russell'], ['Tom Selleck'], ['Michael Douglas']]
    assert actor['tmdb'] == {'title': 'Raiders of the Lost Ark', 'year': 1981}

    director = preview[1]
    assert director['personDepartment'] == 'Directing'

    movie = preview[2]
    assert movie['tmdb'] is None
    assert movie['answerMovies'] == [
        {'title': 'Rocky', 'year': 1976},
        {'title': 'Star Wars', 'year': 1977},
        {'title': 'Jaws', 'year': 1975},
        {'title': 'Alien', 'year': 1979},
    ]

    text_question = preview[3]
    assert 'answerPeople' not in text_question
    assert 'answerMovies' not in text_question

    # Validation is preview-only.
    assert c.get('/api/movie-ladder/questions').json['count'] == 0


def test_movie_ladder_csv_append_persists_and_skips_duplicates(app):
    c = app.test_client()
    payload = {'csv': MOVIE_LADDER_CSV, 'mode': 'append'}

    first = c.post('/api/movie-ladder/admin/questions/import', headers=headers('admin'), json=payload)
    assert first.status_code == 200
    assert first.json == {'ok': True, 'mode': 'append', 'added': 4, 'skipped': 0, 'count': 4}

    duplicate = c.post('/api/movie-ladder/admin/questions/import', headers=headers('admin'), json=payload)
    assert duplicate.status_code == 200
    assert duplicate.json == {'ok': True, 'mode': 'append', 'added': 0, 'skipped': 4, 'count': 4}

    public = c.get('/api/movie-ladder/questions')
    assert public.status_code == 200
    assert public.json['count'] == 4
    assert all(item['id'].startswith('csv-') for item in public.json['questions'])

    reopened = create_app(dict(app.config)).test_client()
    assert reopened.get('/api/movie-ladder/questions').json['count'] == 4


def test_movie_ladder_csv_replace_and_clear(app):
    c = app.test_client()
    assert c.post(
        '/api/movie-ladder/admin/questions/import',
        headers=headers('admin'),
        json={'csv': MOVIE_LADDER_CSV, 'mode': 'append'},
    ).status_code == 200

    one_row = """rung,question,answer_type,answer1,answer2,answer3,answer4,correct,display_title,hero_movie,hero_year
3,How fast must the DeLorean go?,text,77 mph,88 mph,99 mph,100 mph,2,Back to the Future,Back to the Future,1985
"""
    replaced = c.post(
        '/api/movie-ladder/admin/questions/import',
        headers=headers('admin'),
        json={'csv': one_row, 'mode': 'replace'},
    )
    assert replaced.status_code == 200
    assert replaced.json['count'] == 1
    assert replaced.json['added'] == 1
    assert c.get('/api/movie-ladder/questions').json['questions'][0]['movie'] == 'Back to the Future'

    assert c.delete('/api/movie-ladder/admin/questions', headers=headers()).status_code == 403
    cleared = c.delete('/api/movie-ladder/admin/questions', headers=headers('admin'))
    assert cleared.status_code == 200
    assert cleared.json == {'ok': True, 'count': 0}
    assert c.get('/api/movie-ladder/questions').json['count'] == 0


@pytest.mark.parametrize('csv_text, expected', [
    (
        "rung,question,answer_type,answer1,answer2,answer3,answer4,correct\n11,Q?,text,A,B,C,D,1\n",
        'rung must be 1 through 10',
    ),
    (
        "rung,question,answer_type,answer1,answer2,answer3,answer4,correct\n1,Q?,producer,A,B,C,D,1\n",
        'answer_type must be text, actor, director, or movie',
    ),
    (
        "rung,question,answer_type,answer1,answer2,answer3,answer4,correct\n1,Q?,text,A,A,C,D,1\n",
        'answer1 through answer4 must be different',
    ),
    (
        "rung,question,answer_type,answer1,answer2,answer3,answer4,correct\n1,Q?,text,A,B,C,D,5\n",
        'correct must be 1, 2, 3, or 4',
    ),
])
def test_movie_ladder_csv_rejects_bad_rows_without_writing(app, csv_text, expected):
    c = app.test_client()
    result = c.post(
        '/api/movie-ladder/admin/questions/import',
        headers=headers('admin'),
        json={'csv': csv_text, 'mode': 'append'},
    )
    assert result.status_code == 400
    assert expected in result.json['error']
    assert c.get('/api/movie-ladder/questions').json['count'] == 0


def test_movie_ladder_run_history_requires_auth_and_is_user_scoped(app):
    c = app.test_client()
    payload = {
        'id': str(uuid.uuid4()),
        'score': 1200,
        'rungReached': 4,
        'completed': False,
        'livesRemaining': 0,
        'correctCount': 3,
        'wrongCount': 1,
        'maxStreak': 2,
    }

    assert c.post('/api/movie-ladder/runs', json=payload).status_code == 401
    saved = c.post('/api/movie-ladder/runs', headers=headers('player'), json=payload)
    assert saved.status_code == 201
    assert saved.json['run']['rank'] == 'Projectionist'

    player = c.get('/api/movie-ladder/runs', headers=headers('player'))
    assert player.status_code == 200
    assert player.json['summary'] == {
        'totalRuns': 1,
        'bestScore': 1200,
        'highestRung': 4,
        'clears': 0,
    }
    assert len(player.json['recent']) == 1

    other = c.get('/api/movie-ladder/runs', headers=headers('outsider'))
    assert other.status_code == 200
    assert other.json['summary']['totalRuns'] == 0
    assert other.json['recent'] == []


def test_movie_ladder_run_history_best_runs_and_idempotency(app):
    c = app.test_client()

    first_id = str(uuid.uuid4())
    first = {
        'id': first_id,
        'score': 800,
        'rungReached': 3,
        'completed': False,
        'livesRemaining': 0,
        'correctCount': 2,
        'wrongCount': 1,
        'maxStreak': 2,
    }
    assert c.post('/api/movie-ladder/runs', headers=headers(), json=first).status_code == 201
    assert c.post('/api/movie-ladder/runs', headers=headers(), json=first).status_code == 200

    clear = {
        'id': str(uuid.uuid4()),
        'score': 5500,
        'rungReached': 10,
        'completed': True,
        'livesRemaining': 2,
        'correctCount': 10,
        'wrongCount': 0,
        'maxStreak': 10,
    }
    assert c.post('/api/movie-ladder/runs', headers=headers(), json=clear).status_code == 201

    middle = {
        'id': str(uuid.uuid4()),
        'score': 3200,
        'rungReached': 8,
        'completed': False,
        'livesRemaining': 0,
        'correctCount': 7,
        'wrongCount': 1,
        'maxStreak': 4,
    }
    assert c.post('/api/movie-ladder/runs', headers=headers(), json=middle).status_code == 201

    history = c.get('/api/movie-ladder/runs?limit=10', headers=headers()).json
    assert history['summary'] == {
        'totalRuns': 3,
        'bestScore': 5500,
        'highestRung': 10,
        'clears': 1,
    }
    assert history['best'][0]['score'] == 5500
    assert history['best'][0]['rank'] == 'Cinemaster'
    assert history['best'][1]['score'] == 3200
    assert len(history['recent']) == 3


@pytest.mark.parametrize('payload, expected', [
    ({'id': 'bad', 'score': 0, 'rungReached': 1, 'completed': False, 'livesRemaining': 3, 'correctCount': 0, 'wrongCount': 1, 'maxStreak': 0}, 'Run id must be a UUID'),
    ({'id': None, 'score': 0, 'rungReached': 1, 'completed': False, 'livesRemaining': 3, 'correctCount': 0, 'wrongCount': 1, 'maxStreak': 0}, 'Run id must be a UUID'),
    ({'id': str(uuid.uuid4()), 'score': -1, 'rungReached': 1, 'completed': False, 'livesRemaining': 3, 'correctCount': 0, 'wrongCount': 1, 'maxStreak': 0}, 'score must be between'),
    ({'id': str(uuid.uuid4()), 'score': 100, 'rungReached': 11, 'completed': False, 'livesRemaining': 3, 'correctCount': 1, 'wrongCount': 0, 'maxStreak': 1}, 'rungReached must be between'),
    ({'id': str(uuid.uuid4()), 'score': 100, 'rungReached': 5, 'completed': True, 'livesRemaining': 1, 'correctCount': 5, 'wrongCount': 0, 'maxStreak': 5}, 'completed run must reach rung 10'),
])
def test_movie_ladder_run_history_rejects_bad_payloads(app, payload, expected):
    c = app.test_client()
    result = c.post('/api/movie-ladder/runs', headers=headers(), json=payload)
    assert result.status_code == 400
    assert expected in result.json['error']


def movie_ladder_event(*, run_id=None, event_id=None, question_id='builtin-rung-1-1',
                       rung=1, question='Who played Indiana Jones?',
                       answers=None, selected=None, correct=None, answer_type='actor'):
    return {
        'id': event_id or str(uuid.uuid4()),
        'runId': run_id or str(uuid.uuid4()),
        'questionId': question_id,
        'rung': rung,
        'answerType': answer_type,
        'question': question,
        'answers': answers or ['Harrison Ford', 'Kurt Russell', 'Tom Selleck', 'Michael Douglas'],
        'selected': [0] if selected is None else selected,
        'correct': [0] if correct is None else correct,
    }


def test_movie_ladder_question_events_are_anonymous_idempotent_and_aggregated(app):
    c = app.test_client()
    run_id = str(uuid.uuid4())

    correct = movie_ladder_event(run_id=run_id)
    result = c.post('/api/movie-ladder/question-events', json={'events': [correct]})
    assert result.status_code == 201
    assert result.json == {'ok': True, 'received': 1, 'inserted': 1}

    retry = c.post('/api/movie-ladder/question-events', json={'events': [correct]})
    assert retry.status_code == 200
    assert retry.json == {'ok': True, 'received': 1, 'inserted': 0}

    wrong = movie_ladder_event(
        run_id=str(uuid.uuid4()),
        event_id=str(uuid.uuid4()),
        selected=[1],
    )
    assert c.post('/api/movie-ladder/question-events', json={'events': [wrong]}).status_code == 201

    assert c.get('/api/movie-ladder/admin/question-stats').status_code == 401
    assert c.get('/api/movie-ladder/admin/question-stats', headers=headers()).status_code == 403

    stats = c.get('/api/movie-ladder/admin/question-stats', headers=headers('admin'))
    assert stats.status_code == 200
    assert stats.json['summary'] == {
        'questionsSeen': 1,
        'attempts': 2,
        'correct': 1,
        'wrong': 1,
        'accuracyPercent': 50.0,
    }
    item = stats.json['questions'][0]
    assert item['questionId'] == 'builtin-rung-1-1'
    assert item['rung'] == 1
    assert item['answerType'] == 'actor'
    assert item['attempts'] == 2
    assert item['correct'] == 1
    assert item['wrong'] == 1
    assert item['accuracyPercent'] == 50.0


def test_movie_ladder_question_events_validate_imported_question_snapshot(app):
    c = app.test_client()
    imported = c.post(
        '/api/movie-ladder/admin/questions/import',
        headers=headers('admin'),
        json={'csv': MOVIE_LADDER_CSV, 'mode': 'replace'},
    )
    assert imported.status_code == 200

    question = c.get('/api/movie-ladder/questions').json['questions'][0]
    event = movie_ladder_event(
        question_id=question['id'],
        rung=question['rung'],
        question=question['question'],
        answers=question['answers'],
        selected=[question['correct']],
        correct=[question['correct']],
        answer_type='actor',
    )
    saved = c.post('/api/movie-ladder/question-events', json={'events': [event]})
    assert saved.status_code == 201

    tampered = dict(event)
    tampered['id'] = str(uuid.uuid4())
    tampered['runId'] = str(uuid.uuid4())
    tampered['question'] = 'Different question text'
    rejected = c.post('/api/movie-ladder/question-events', json={'events': [tampered]})
    assert rejected.status_code == 400
    assert 'does not match the active bank' in rejected.json['error']


def test_movie_ladder_question_events_support_ordered_timeline_answers(app):
    c = app.test_client()
    event = movie_ladder_event(
        question_id='builtin-rung-5-5',
        rung=5,
        question='Tap these movies in release order.',
        answers=['The Godfather', 'Chinatown', 'Taxi Driver', 'Network'],
        selected=[0, 1, 2, 3],
        correct=[0, 1, 2, 3],
        answer_type='timeline',
    )
    saved = c.post('/api/movie-ladder/question-events', json={'events': [event]})
    assert saved.status_code == 201

    stats = c.get('/api/movie-ladder/admin/question-stats', headers=headers('admin')).json
    assert stats['questions'][0]['answerType'] == 'timeline'
    assert stats['questions'][0]['accuracyPercent'] == 100.0


@pytest.mark.parametrize('mutator, expected', [
    (lambda event: event.update(questionId='not-real'), 'Question id is not recognized'),
    (lambda event: event.update(rung=11), 'rung must be between 1 and 10'),
    (lambda event: event.update(answerType='producer'), 'answerType must be text, actor, director, movie, or timeline'),
    (lambda event: event.update(selected=[4]), 'selected answer indexes must be 0 through 3'),
    (lambda event: event.update(selected=[0, 0, 1, 2]), 'selected ordered indexes must be unique'),
    (lambda event: event.update(selected=[0], correct=[0, 1, 2, 3]), 'selected and correct must use the same answer format'),
])
def test_movie_ladder_question_events_reject_bad_payloads(app, mutator, expected):
    c = app.test_client()
    event = movie_ladder_event()
    mutator(event)
    result = c.post('/api/movie-ladder/question-events', json={'events': [event]})
    assert result.status_code == 400
    assert expected in result.json['error']
