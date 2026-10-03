from test_api import app, headers, submit


def test_public_history_record_milestones_privacy_corrections_and_removal(app):
    c=app.test_client();url='/api/games/galaga/history'
    first=c.get(url);assert first.status_code==200
    assert first.json['recordHistory'][0]['imported'] is True
    assert first.json['recordHistory'][0]['createdAt'] is None
    submit(c,score='100',initials='LOW')
    win=submit(c,score='50000',initials='WIN').json['record']
    submit(c,score='50000',initials='TIE')
    payload=c.get(url).json
    assert len(payload['recordHistory'])==2
    assert payload['currentRecord']['initials']=='WIN'
    assert payload['recordHistory'][0]['score']=='50,000'
    for entry in payload['recordHistory']:
        assert set(entry)=={'id','score','initials','createdAt','imported','corrected'}
    assert 'email' not in str(payload) and 'photoId' not in str(payload)
    assert c.patch('/api/admin/scores/'+win['id'],json={'revision':win['revision'],'score':'51000','initials':'FIX'},headers=headers('admin')).status_code==200
    payload=c.get(url).json
    assert payload['currentRecord']['score']=='51,000'
    assert payload['recordHistory'][0]['score']=='50,000' and payload['recordHistory'][0]['corrected']
    assert c.delete('/api/admin/scores/'+win['id'],json={'revision':win['revision']+1},headers=headers('admin')).status_code==200
    assert win['id'] not in [e['id'] for e in c.get(url).json['recordHistory']]
    assert c.get('/api/games/no-such-game/history').status_code==404


def test_empty_game_and_fastest_time_history(app):
    c=app.test_client()
    game=c.post('/api/admin/games',json={'title':'History time test','kind':'time'},headers=headers('admin')).json['game']
    url='/api/games/'+game['id']+'/history'
    assert c.get(url).json['currentRecord'] is None and c.get(url).json['recordHistory']==[]
    submit(c,score='1:10.00',game=game['id'])
    submit(c,score='1:20.00',game=game['id'])
    submit(c,score='1:02.30',game=game['id'])
    result=c.get(url).json
    assert len(result['recordHistory'])==2 and result['currentRecord']['score']=='1:02.30'
