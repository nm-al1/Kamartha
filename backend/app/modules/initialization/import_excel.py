"""Bounded template reader and atomic, previewed opening-data import."""
from datetime import date
from io import BytesIO
import json
import posixpath
import re
import zlib
from uuid import NAMESPACE_URL, uuid5
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import text

from app.core.errors import AppError
from app.core.idempotency import payload_hash
from app.modules.initialization.schemas import OpeningRecord
from app.modules.initialization.service import encode_draft, reconciliation
from app.modules.residents.schemas import ResidentInput
from app.modules.rooms.schemas import RoomInput


MAX_FILE = 2 * 1024 * 1024
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
HEADERS = {
    'Kamar': ['Nomor kamar'],
    'Penghuni': ['Kode penghuni', 'Nama', 'Jenis identitas', 'Nomor identitas', 'WhatsApp (opsional)', 'Catatan (opsional)'],
    'Kontrak': ['Kode kontrak', 'Nomor kamar', 'Jumlah penghuni paket', 'Paket bulan', 'Tanggal mulai', 'Tanggal akhir eksklusif', 'Harga paket (otomatis)'],
    'Penempatan': ['Kode kontrak', 'Kode penghuni', 'Penanggung jawab', 'Tanggal masuk', 'Status tinggal', 'Tanggal keluar (jika ada)', 'Keluar tidak diketahui'],
    'Sisa tagihan awal': ['Kode kontrak', 'Awal periode', 'Jatuh tempo', 'Nilai tagihan', 'Sisa belum dibayar', 'Sudah dibayar (otomatis)'],
}
INPUT_COLUMNS = {'Kamar': 1, 'Penghuni': 6, 'Kontrak': 6, 'Penempatan': 7, 'Sisa tagihan awal': 5}
PRICES = {(1, 1): 700000, (1, 6): 3500000, (1, 12): 7000000,
          (2, 1): 1000000, (2, 6): 5500000, (2, 12): 10000000}


def invalid(message):
    raise AppError('IMPORT_INVALID', message, 422)


def stable_id(kind, value):
    return uuid5(NAMESPACE_URL, f'kamartha:opening-import:{kind}:{value}')


def read_workbook(content):
    if not content or len(content) > MAX_FILE:
        invalid('Berkas Excel maksimal 2 MB dan tidak boleh kosong.')
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if (len(entries) > 100 or len({e.filename for e in entries}) != len(entries)
                    or sum(e.file_size for e in entries) > 12 * 1024 * 1024
                    or any('vbaproject' in e.filename.lower() or 'externallinks/' in e.filename.lower() for e in entries)):
                invalid('Struktur Excel terlalu besar atau tidak didukung.')

            def xml(path):
                data = archive.read(path)
                if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                    invalid('Deklarasi XML eksternal tidak diperbolehkan.')
                return ET.fromstring(data)

            book = xml('xl/workbook.xml')
            relations = {n.attrib['Id']: n.attrib['Target'] for n in xml('xl/_rels/workbook.xml.rels')
                         if n.attrib.get('TargetMode') != 'External'}
            shared = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                shared = [''.join(n.itertext()) for n in xml('xl/sharedStrings.xml')]
            sheets = book.find(NS + 'sheets')
            names = [n.attrib['name'] for n in sheets]
            if len(set(names)) != len(names) or not set(HEADERS).issubset(names):
                invalid('Gunakan sheet dan header dari template KAMARTHA.')
            tables = {}
            for node in sheets:
                name = node.attrib['name']
                if name not in HEADERS:
                    continue
                relation = node.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
                target = relations[relation]
                path = posixpath.normpath(target.lstrip('/') if target.startswith('/') else 'xl/' + target)
                if not path.startswith('xl/worksheets/'):
                    invalid('Referensi sheet tidak didukung.')
                rows = {}
                for row in xml(path).find(NS + 'sheetData'):
                    number = int(row.attrib['r'])
                    if not 1 <= number <= 201 or number in rows:
                        invalid(f'{name}: maksimal 200 baris isian; nomor baris harus unik.')
                    values = [None] * len(HEADERS[name])
                    seen = set()
                    for c in row:
                        address = c.attrib['r']
                        match = re.fullmatch(r'([A-Z]+)(\d+)', address)
                        if not match or int(match[2]) != number:
                            invalid('Alamat sel tidak sah.')
                        index = 0
                        for char in match[1]:
                            index = index * 26 + ord(char) - 64
                        index -= 1
                        if index in seen or index >= len(values):
                            invalid(f'{name}: kolom tidak sesuai template.')
                        seen.add(index)
                        if number > 1 and index >= INPUT_COLUMNS[name]:
                            continue  # Derived prices and paid totals are recomputed, never trusted.
                        if c.find(NS + 'f') is not None:
                            invalid(f'{name} baris {number}: formula hanya boleh pada kolom otomatis.')
                        kind = c.attrib.get('t')
                        v = c.findtext(NS + 'v')
                        if name == 'Penghuni' and number > 1 and index in (3, 4) and v is not None and kind not in ('s', 'str', 'inlineStr'):
                            invalid(f'{name} baris {number}: nomor identitas/WhatsApp harus berformat teks agar nol awal tidak hilang.')
                        if kind == 'inlineStr':
                            value = ''.join(c.find(NS + 'is').itertext())
                        elif kind == 's':
                            value = shared[int(v)]
                        elif kind in ('b', 'e'):
                            invalid(f'{name} baris {number}: tipe sel tidak didukung.')
                        else:
                            value = v
                        if value is not None and len(value) > 10000:
                            invalid(f'{name} baris {number}: teks terlalu panjang.')
                        values[index] = value
                    rows[number] = values
                if rows.get(1) != HEADERS[name]:
                    invalid(f'{name}: header harus persis seperti template.')
                data = [rows.get(i, [None] * len(HEADERS[name]))[:INPUT_COLUMNS[name]]
                        for i in range(2, max(rows) + 1)]
                while data and not any(v not in (None, '') for v in data[-1]):
                    data.pop()
                tables[name] = data
            return tables
    except AppError:
        raise
    except (BadZipFile, KeyError, ValueError, IndexError, TypeError, AttributeError, ET.ParseError, RuntimeError, NotImplementedError, OverflowError, OSError, EOFError, zlib.error):
        invalid('Berkas bukan Excel .xlsx yang didukung. Gunakan template KAMARTHA.')


def plan_import(db, settings, today, tables):
    """No writes: project imported rows through the existing reconciliation rules."""
    if set(tables) != set(HEADERS) or any(len(rows) > 200 for rows in tables.values()):
        invalid('Sheet tidak sesuai template atau melebihi 200 baris.')
    if len(json.dumps(tables).encode()) > MAX_FILE:
        invalid('Isian impor terlalu besar.')
    rooms = [dict(r) for r in db.execute(text('SELECT * FROM kamartha.rooms ORDER BY id')).mappings()]
    residents = [dict(r) for r in db.execute(text('SELECT * FROM kamartha.residents ORDER BY id')).mappings()]
    packages = [dict(r) for r in db.execute(text('SELECT * FROM kamartha.packages ORDER BY id')).mappings()]
    drafts = [dict(r) for r in db.execute(text('SELECT * FROM kamartha.initialization_records ORDER BY id')).mappings()]
    fingerprint = payload_hash(jsonable_encoder({'settings': dict(settings), 'rooms': rooms,
        'residents': residents, 'packages': packages, 'drafts': drafts, 'tables': tables, 'today': today}))
    errors, room_map, resident_map, contract_map = [], {}, {}, {}
    new_rooms, new_residents, new_drafts, preview = [], [], [], []

    def issue(sheet, row, message):
        errors.append({'sheet': sheet, 'row': row, 'message': message})

    def required(value):
        value = '' if value is None else str(value).strip()
        if not value or len(value) > 10000:
            raise ValueError('Isian wajib kosong atau terlalu panjang.')
        return value

    def integer(value):
        raw = required(value)
        if not re.fullmatch(r'\d{1,13}', raw):
            raise ValueError('Gunakan angka bulat tanpa Rp, titik, atau pecahan.')
        result = int(raw)
        if result > 1_000_000_000_000:
            raise ValueError('Nominal melebihi batas aplikasi.')
        return result

    def day(value):
        raw = required(value)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
            raise ValueError('Tanggal harus YYYY-MM-DD, bukan nomor tanggal Excel.')
        try:
            return date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError('Tanggal kalender tidak sah.') from exc

    def choice(value, choices):
        raw = required(value)
        if raw not in choices:
            raise ValueError('Pilihan tidak sesuai template.')
        return raw

    def rows(sheet):
        for number, row in enumerate(tables[sheet], 2):
            if len(row) != INPUT_COLUMNS[sheet]:
                invalid(f'{sheet} baris {number}: jumlah kolom tidak sesuai.')
            if any(v not in (None, '') for v in row):
                yield number, row

    for number, row in rows('Kamar'):
        try:
            value = RoomInput(number=required(row[0]), room_type='Standar', supported_occupants=2, reference_price=700000)
            key = value.number.lower()
            if key in room_map:
                raise ValueError('Nomor kamar ganda dalam berkas.')
            existing = next((r for r in rooms if r['number'].lower() == key), None)
            if existing and (existing['room_type'] != 'Standar' or existing['supported_occupants'] != 2):
                raise ValueError('Kamar sudah ada dengan tipe/kapasitas berbeda. Tidak ditimpa.')
            item = existing or {'id': stable_id('room', key), **value.model_dump(), 'number_normalized': key}
            room_map[key] = item
            if not existing:
                new_rooms.append(item)
            preview.append({'sheet': 'Kamar', 'row': number, 'label': value.number, 'status': 'EXISTING' if existing else 'NEW'})
        except (ValueError, ValidationError) as exc:
            issue('Kamar', number, 'Isian kamar tidak sah.' if isinstance(exc, ValidationError) else str(exc))

    seen_identities = set()
    for number, row in rows('Penghuni'):
        try:
            code = required(row[0])
            value = ResidentInput(name=required(row[1]), identity_type=required(row[2]), identity_number=required(row[3]),
                                  whatsapp_number=str(row[4]).strip() if row[4] else None, notes=str(row[5]).strip() if row[5] else None)
            identity = (value.identity_type.casefold(), value.identity_number.casefold())
            if code in resident_map or identity in seen_identities:
                raise ValueError('Kode atau identitas penghuni ganda dalam berkas.')
            matches = [r for r in residents if (r['identity_type'].casefold(), r['identity_number'].casefold()) == identity]
            if len(matches) > 1:
                raise ValueError('Identitas cocok ke beberapa penghuni; perlu pemeriksaan manual.')
            existing = matches[0] if matches else None
            if existing and any(existing[k] != v for k, v in value.model_dump().items()):
                raise ValueError('Identitas sudah ada dengan isian berbeda. Data lama tidak ditimpa.')
            item = existing or {'id': stable_id('resident', json.dumps(identity)), **value.model_dump()}
            resident_map[code] = item
            seen_identities.add(identity)
            if not existing:
                new_residents.append(item)
            preview.append({'sheet': 'Penghuni', 'row': number, 'label': f'{code}: {value.name}', 'status': 'EXISTING' if existing else 'NEW'})
        except (ValueError, ValidationError) as exc:
            issue('Penghuni', number, 'Isian penghuni tidak sah.' if isinstance(exc, ValidationError) else str(exc))

    for number, row in rows('Kontrak'):
        try:
            code, room_number = required(row[0]), required(row[1]).lower()
            if code in contract_map:
                raise ValueError('Kode kontrak ganda.')
            if room_number not in room_map:
                raise ValueError('Nomor kamar harus tercantum di sheet Kamar.')
            people, months = integer(row[2]), integer(row[3])
            if (people, months) not in PRICES:
                raise ValueError('Paket harus 1/2 orang dengan durasi 1/6/12 bulan.')
            matches = [p for p in packages if p['is_active'] and p['occupant_type'] == people and p['period_months'] == months]
            if len(matches) != 1:
                raise ValueError('Paket aktif tidak tersedia atau ambigu di aplikasi.')
            starts, ends = day(row[4]), day(row[5])
            if (ends - starts).days > 36600:
                raise ValueError('Rentang satu kontrak impor maksimal 100 tahun.')
            contract_map[code] = {'row': number, 'key': stable_id('contract', code), 'room_id': room_map[room_number]['id'],
                'package_id': matches[0]['id'], 'starts_on': starts, 'ends_on': ends,
                'price': PRICES[people, months], 'occupancies': [], 'invoices': [], 'responsible': []}
        except ValueError as exc:
            issue('Kontrak', number, str(exc))

    for number, row in rows('Penempatan'):
        try:
            code, resident = required(row[0]), required(row[1])
            if code not in contract_map or resident not in resident_map:
                raise ValueError('Kode kontrak/penghuni tidak ditemukan dalam sheet terkait.')
            responsible = choice(row[2], ('Ya', 'Tidak')) == 'Ya'
            state = choice(row[4], ('Tinggal', 'Keluar'))
            unknown = choice(row[6], ('Ya', 'Tidak')) == 'Ya'
            occupancy = {'resident_id': resident_map[resident]['id'], 'entered_on': day(row[3]),
                         'state': 'STAYING' if state == 'Tinggal' else 'EXITED',
                         'exited_on': day(row[5]) if row[5] else None, 'exit_date_unknown': unknown}
            contract_map[code]['occupancies'].append(occupancy)
            if responsible:
                contract_map[code]['responsible'].append(occupancy['resident_id'])
        except ValueError as exc:
            issue('Penempatan', number, str(exc))

    for number, row in rows('Sisa tagihan awal'):
        try:
            code = required(row[0])
            if code not in contract_map:
                raise ValueError('Kode kontrak tidak ditemukan.')
            amount, remaining = integer(row[3]), integer(row[4])
            if amount <= 0 or remaining > amount:
                raise ValueError('Nilai tagihan harus positif dan sisa tidak boleh melebihi tagihan.')
            contract_map[code]['invoices'].append({'period_start': day(row[1]), 'due_on': day(row[2]),
                                                 'amount': amount, 'opening_paid': amount - remaining})
        except ValueError as exc:
            issue('Sisa tagihan awal', number, str(exc))

    for code, item in contract_map.items():
        try:
            if len(item['responsible']) != 1:
                raise ValueError('Pilih tepat satu penanggung jawab pada sheet Penempatan.')
            record = OpeningRecord.model_validate({k: v for k, v in item.items() if k not in ('row', 'key', 'responsible')} |
                                                 {'responsible_resident_id': item['responsible'][0]})
            data = record.model_dump(mode='json')
            existing = next((d for d in drafts if d['client_record_key'] == item['key']), None)
            if existing and payload_hash(existing['draft_data']) != payload_hash(data):
                raise ValueError('Kode kontrak impor sudah digunakan dengan data berbeda. Tidak ditimpa.')
            if not existing:
                new_drafts.append({'id': item['key'], 'client_record_key': item['key'], 'draft_data': data})
            preview.append({'sheet': 'Kontrak', 'row': item['row'], 'label': code,
                'status': 'EXISTING' if existing else 'NEW', 'price': record.price,
                'room_number': next(r['number'] for r in room_map.values() if r['id'] == record.room_id),
                'residents': [r['name'] for r in resident_map.values() if r['id'] in {o.resident_id for o in record.occupancies}],
                'occupants': [{**o.model_dump(mode='json'),
                    'name': next(r['name'] for r in resident_map.values() if r['id'] == o.resident_id)} for o in record.occupancies],
                'remaining': sum(i.amount - i.opening_paid for i in record.invoices), 'data': data})
        except (ValueError, ValidationError) as exc:
            issue('Kontrak', item['row'], 'Isian kontrak belum lengkap atau tidak sah.' if isinstance(exc, ValidationError) else str(exc))

    if not contract_map:
        issue('Kontrak', 1, 'Isi minimal satu kontrak untuk mengimpor data awal.')
    projected = {'rooms': rooms + new_rooms, 'residents': residents + new_residents,
                 'packages': packages, 'drafts': drafts + new_drafts}
    summary, _ = reconciliation(db, settings, today, projected=projected)
    row_by_id = {str(item['key']): item['row'] for item in contract_map.values()}
    for problem in summary['errors']:
        issue('Kontrak', row_by_id.get(problem['record_id']), ' '.join(problem['messages']))
    result = {'tables': tables, 'preview_hash': fingerprint, 'can_import': not errors, 'errors': errors,
              'items': preview, 'new_rooms': len(new_rooms), 'new_residents': len(new_residents),
              'new_records': len(new_drafts), 'total_receivable': summary['total_receivable'],
              'cutover_date': settings['cutover_date']}
    return jsonable_encoder(result), (new_rooms, new_residents, new_drafts)


def save_import(db, manager_id, changes):
    rooms, residents, drafts = changes
    for item in rooms:
        db.execute(text('''INSERT INTO kamartha.rooms
            (id,number,number_normalized,room_type,supported_occupants,reference_price,is_available_for_new_lease)
            VALUES (:id,:number,:number_normalized,:room_type,:supported_occupants,:reference_price,:is_available_for_new_lease)'''), item)
    for item in residents:
        db.execute(text('''INSERT INTO kamartha.residents (id,name,identity_type,identity_number,whatsapp_number,notes)
            VALUES (:id,:name,:identity_type,:identity_number,:whatsapp_number,:notes)'''), item)
    for item in drafts:
        db.execute(text('''INSERT INTO kamartha.initialization_records (client_record_key,draft_data,created_by)
            VALUES (:key,CAST(:data AS JSONB),:manager)'''),
                   {'key': item['client_record_key'], 'data': encode_draft(item['draft_data']), 'manager': manager_id})
    if rooms or residents or drafts:
        db.execute(text('UPDATE kamartha.app_settings SET version=version+1 WHERE id=1'))
    return {'created_rooms': len(rooms), 'created_residents': len(residents), 'created_records': len(drafts)}
