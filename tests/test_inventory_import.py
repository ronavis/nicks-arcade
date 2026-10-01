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
    assert len(c.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])==19
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
    assert len(c.get('/api/admin/cabinets',headers=headers('admin')).json['cabinets'])==19


def test_stale_preview_and_unicode_csv(app):
    c=app.test_client();source='\ufeffGame,Cabinet 1\r\n"New, Game","Ron’s Cabinet"\r\n'
    p=call(c,source).json
    assert not p['errors']
    c.post('/api/admin/cabinets',json={'name':'Ron’s Cabinet'},headers=headers('admin'))
    assert call(c,source,'commit',previewHash=p['previewHash']).status_code==409
    p=call(c,source).json
    assert call(c,source,'commit',previewHash=p['previewHash']).status_code==200
    assert call(c,source).json['counts']==dict(games=0,cabinets=0,assignments=0)


def test_excel_template_preview_commit_and_repeat(app):
    import io
    from pathlib import Path
    c = app.test_client()
    workbook = Path('templates/arcade-inventory-template.xlsx').read_bytes()
    def preview(token='admin', content=workbook):
        return c.post('/api/admin/inventory-import', data={'mode':'preview','file':(io.BytesIO(content),'inventory.xlsx')}, headers=headers(token))
    assert preview('player').status_code == 403
    result = preview()
    assert result.status_code == 200, result.json
    p = result.json
    assert not p['errors'] and len(p['rows']) == 3
    assert call(c,p['csv'],'commit',previewHash=p['previewHash']).status_code == 200
    assert preview().json['counts'] == dict(games=0,cabinets=0,assignments=0)
    for bad in [b'not a workbook', b'x'*(2097153)]:
        assert preview(content=bad).status_code == 400


def test_populated_excel_matches_csv(app):
    from pathlib import Path
    from server.inventory_workbook import workbook_csv
    c = app.test_client()
    csv = workbook_csv(Path('templates/nicks-arcade-inventory-2026-10-01.xlsx').read_bytes())
    actual = call(c,csv).json
    expected = call(c,Path('templates/nicks-arcade-inventory-2026-10-01.csv').read_text()).json
    assert len(actual['rows']) == 98 and not actual['errors']
    assert actual['previewHash'] == expected['previewHash']


def test_excel_rejects_missing_games_formulas_and_unsafe_xml(app):
    import io
    import zipfile
    from pathlib import Path
    original = Path('templates/arcade-inventory-template.xlsx').read_bytes()
    def changed(path, transform):
        out=io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(out,'w') as dest:
            for name in source.namelist():
                value=source.read(name)
                dest.writestr(name,transform(value) if name==path else value)
        return out.getvalue()
    c=app.test_client()
    cases=[changed('xl/workbook.xml',lambda s:s.replace(b'name="Games"',b'name="Other"')),
           changed('xl/worksheets/sheet1.xml',lambda s:s.replace(b'</x:c>',b'<x:f>1+1</x:f></x:c>',1)),
           changed('xl/workbook.xml',lambda s:b'<!DOCTYPE workbook [<!ENTITY test "x">]>'+s)]
    for content in cases:
        result=c.post('/api/admin/inventory-import',data={'mode':'preview','file':(io.BytesIO(content),'test.xlsx')},headers=headers('admin'))
        assert result.status_code==400,result.json
