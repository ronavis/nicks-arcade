"""Read the template's Games worksheet into the existing bounded CSV import path."""
import csv
import io
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def workbook_csv(data):
    if len(data) > 2 * 1024 * 1024:
        raise ValueError('Choose an Excel workbook under 2 MB.')
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 250 or sum(e.file_size for e in entries) > 10 * 1024 * 1024:
                raise ValueError('This workbook is too large. Use the arcade template with up to 500 game rows.')
            if len({e.filename for e in entries}) != len(entries):
                raise ValueError('The workbook contains duplicate files. Save a fresh copy in Excel.')

            def xml(path):
                text = archive.read(path).decode('utf-8-sig')
                if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
                    raise ValueError('This workbook XML is unsupported. Save a fresh .xlsx copy.')
                return ET.fromstring(text)

            book = xml('xl/workbook.xml')
            sheets = [s for s in book.findall(f'{NS}sheets/{NS}sheet') if s.get('name', '').strip().lower() == 'games']
            if len(sheets) != 1:
                raise ValueError('Use the Excel template with a worksheet named Games. Only that sheet is imported.')
            relations = xml('xl/_rels/workbook.xml.rels')
            rel = next((r for r in relations if r.get('Id') == sheets[0].get(REL + 'id')), None)
            if rel is None or rel.get('TargetMode') == 'External':
                raise ValueError('The Games worksheet could not be read.')
            target = rel.get('Target', '')
            path = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/' + target)
            if not path.startswith('xl/worksheets/'):
                raise ValueError('The Games worksheet location is unsupported.')
            shared = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                shared = [''.join(t.text or '' for t in item.iter(NS+'t')) for item in xml('xl/sharedStrings.xml')]
            cells, last = {}, 0
            for cell in xml(path).iter(NS+'c'):
                if cell.find(NS+'f') is not None:
                    raise ValueError('Use plain values in Games, not formulas. Paste values and preview again.')
                kind = cell.get('t')
                raw = cell.findtext(NS+'v', '')
                if kind == 's':
                    index = int(raw)
                    if index < 0 or index >= len(shared):
                        raise ValueError('The Games worksheet contains an invalid text reference.')
                    value = shared[index]
                elif kind == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.iter(NS+'t'))
                elif kind == 'e':
                    raise ValueError('Fix spreadsheet errors in the Games sheet before importing.')
                else:
                    value = raw
                if not value.strip():
                    continue
                match = re.fullmatch(r'([A-Z]+)([1-9][0-9]*)', cell.get('r', ''))
                if not match:
                    raise ValueError('The Games worksheet contains an invalid cell address.')
                col, row = match.group(1), int(match.group(2))
                if len(col) != 1 or col > 'F' or row > 501:
                    raise ValueError('Use the six template columns and at most 500 game rows in Games.')
                address = (row, ord(col)-65)
                if address in cells:
                    raise ValueError('The Games worksheet contains duplicate cells.')
                cells[address] = value
                last = max(last, row)
            output = io.StringIO()
            writer = csv.writer(output)
            for row in range(1, last+1):
                writer.writerow([cells.get((row, col), '') for col in range(6)])
            return output.getvalue()
    except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeError, RuntimeError, OSError) as exc:
        raise ValueError('This Excel file could not be read. Use an unencrypted .xlsx copy of the arcade template.') from exc
