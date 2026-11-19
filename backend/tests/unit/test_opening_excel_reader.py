from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from app.core.errors import AppError
from app.modules.initialization.import_excel import read_workbook


TEMPLATE = Path(__file__).resolve().parents[3] / 'docs/templates/KAMARTHA-contoh-dummy-5-kamar.xlsx'


def test_reads_template_without_trusting_calculated_prices():
    tables = read_workbook(TEMPLATE.read_bytes())
    assert len(tables['Kamar']) == 5
    assert len(tables['Penghuni']) == 8
    assert len(tables['Kontrak']) == 5
    assert len(tables['Kontrak'][0]) == 6
    assert len(tables['Sisa tagihan awal'][0]) == 5


@pytest.mark.parametrize('data', [b'not Excel', b'', b'a' * (2 * 1024 * 1024 + 1)])
def test_rejects_invalid_or_oversize_file(data):
    with pytest.raises(AppError):
        read_workbook(data)


@pytest.mark.parametrize('replacement', [
    b'<f>HYPERLINK("https://example.com")</f>',
    b'<is><t>Kolom salah</t></is>',
])
def test_rejects_formula_or_changed_headers(replacement):
    result = BytesIO()
    with ZipFile(TEMPLATE) as source, ZipFile(result, 'w', ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == 'xl/worksheets/sheet3.xml':
                data = data.replace(b'<is><t>Nomor kamar</t></is>', replacement)
            target.writestr(name, data)
    with pytest.raises(AppError):
        read_workbook(result.getvalue())


@pytest.mark.parametrize('mutation', ['xml_entity', 'too_many_rows', 'expanded_size', 'macro', 'duplicate_entry'])
def test_archive_and_xml_resource_guards(mutation):
    result = BytesIO()
    with ZipFile(TEMPLATE) as source, ZipFile(result, 'w', ZIP_DEFLATED) as target:
        for name in source.namelist():
            data = source.read(name)
            if name == 'xl/worksheets/sheet3.xml':
                if mutation == 'xml_entity':
                    data = data.replace(b'<worksheet', b'<!DOCTYPE worksheet [<!ENTITY x "expansion">]><worksheet', 1)
                elif mutation == 'too_many_rows':
                    data = data.replace(b'r="201"', b'r="202"')
            target.writestr(name, data)
        if mutation == 'expanded_size':
            target.writestr('large.xml', b' ' * (13 * 1024 * 1024))
        elif mutation == 'macro':
            target.writestr('xl/vbaProject.bin', b'test')
        elif mutation == 'duplicate_entry':
            with pytest.warns(UserWarning):
                target.writestr('xl/workbook.xml', source.read('xl/workbook.xml'))
    with pytest.raises(AppError):
        read_workbook(result.getvalue())
