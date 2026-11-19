import json

from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import text

from app.core.idempotency import payload_hash
from app.core.errors import AppError
from app.modules.billing.rules import period_boundary
from app.modules.initialization.rules import occupancy_end, overlaps, validate_record
from app.modules.initialization.schemas import OpeningRecord


def reconciliation(db, settings, today, *, projected=None):
    rooms = {row['id']: row for row in (projected['rooms'] if projected is not None else db.execute(text('SELECT * FROM kamartha.rooms')).mappings())}
    residents = {row['id']: row for row in (projected['residents'] if projected is not None else db.execute(text('SELECT id,name FROM kamartha.residents')).mappings())}
    packages = {row['id']: row for row in (projected['packages'] if projected is not None else db.execute(text('SELECT * FROM kamartha.packages')).mappings())}
    drafts = projected['drafts'] if projected is not None else db.execute(text('SELECT * FROM kamartha.initialization_records ORDER BY id')).mappings().all()
    errors, valid = [], []
    cutover = settings['cutover_date']
    if cutover is None or cutover > today:
        errors.append({'record_id': None, 'messages': ['Tanggal mulai pencatatan wajib diisi dan tidak di masa depan.']})
    for draft in drafts:
        messages = []
        try:
            record = OpeningRecord.model_validate(draft['draft_data'])
        except ValidationError as exc:
            messages = ['Isian belum lengkap: ' + '.'.join(map(str, e['loc'])) for e in exc.errors()]
            errors.append({'record_id': str(draft['id']), 'messages': messages})
            continue
        room, package = rooms.get(record.room_id), packages.get(record.package_id)
        if room is None or package is None or not package['is_active']:
            messages.append('Kamar atau paket tidak tersedia.')
        if any(o.resident_id not in residents for o in record.occupancies):
            messages.append('Penghuni tidak ditemukan.')
        if room and package and cutover:
            messages += validate_record(record, cutover=cutover, today=today,
                                        occupant_type=package['occupant_type'], period_months=package['period_months'],
                                        capacity=room['supported_occupants'])
        if messages:
            errors.append({'record_id': str(draft['id']), 'messages': messages})
        else:
            valid.append((draft, record, package))
    for i, (draft, record, _) in enumerate(valid):
        for other_draft, other, _ in valid[i + 1:]:
            messages = []
            if record.room_id == other.room_id:
                if overlaps(record.starts_on, record.ends_on, other.starts_on, other.ends_on):
                    messages.append('Kontrak kamar bertumpuk dengan berkas lain.')
                older, newer = (record, other) if record.starts_on <= other.starts_on else (other, record)
                if any(o.state == 'STAYING' or (o.exited_on and o.exited_on > newer.starts_on)
                       for o in older.occupancies):
                    messages.append('Kamar masih tertahan penghunian kontrak sebelumnya.')
            for occupancy in record.occupancies:
                for other_occupancy in other.occupancies:
                    if occupancy.resident_id == other_occupancy.resident_id and overlaps(
                        occupancy.entered_on, occupancy_end(occupancy, record.ends_on),
                        other_occupancy.entered_on, occupancy_end(other_occupancy, other.ends_on),
                    ):
                        messages.append('Penghunian orang bertumpuk dengan berkas lain.')
            if messages:
                errors.append({'record_id': str(draft['id']), 'other_record_id': str(other_draft['id']),
                               'messages': list(dict.fromkeys(messages))})
    summary = {
        'version': settings['version'], 'cutover_date': cutover,
        'record_count': len(drafts), 'resident_count': len({o.resident_id for _, r, _ in valid for o in r.occupancies}),
        'occupied_room_count': len({r.room_id for _, r, _ in valid if any(o.state == 'STAYING' for o in r.occupancies)}),
        'invoice_count': sum(len(r.invoices) for _, r, _ in valid),
        'total_receivable': sum(i.amount - i.opening_paid for _, r, _ in valid for i in r.invoices),
        'errors': errors, 'can_finalize': not errors,
        'records': [{
            'record_id': str(draft['id']), 'room_number': rooms[record.room_id]['number'],
            'starts_on': record.starts_on, 'ends_on': record.ends_on, 'price': record.price,
            'occupant_type': package['occupant_type'], 'period_months': package['period_months'],
            'occupancies': [{**o.model_dump(), 'name': residents[o.resident_id]['name']} for o in record.occupancies],
            'invoices': [{**i.model_dump(), 'remaining': i.amount - i.opening_paid} for i in record.invoices],
        } for draft, record, package in valid],
    }
    summary['reconciliation_hash'] = payload_hash(jsonable_encoder({
        'summary': summary, 'drafts': [dict(d) for d in drafts],
        'rooms': [dict(rooms[key]) for key in sorted(rooms)], 'residents': sorted(map(str, residents)),
        'packages': [dict(packages[key]) for key in sorted(packages)],
    }))
    return summary, valid


def materialize(db, valid, manager_id):
    for draft, record, package in valid:
        params = {'room': record.room_id, 'package': record.package_id, 'start': record.starts_on,
                  'end': record.ends_on, 'occupants': package['occupant_type'], 'months': package['period_months'],
                  'price': record.price, 'draft': draft['id'], 'manager': manager_id}
        lease = db.scalar(text('''
            INSERT INTO kamartha.leases(room_id,package_id,starts_on,agreed_ends_on,effective_ends_on,
                period_anchor,occupant_type_snapshot,period_months_snapshot,period_price_snapshot,
                source,initialization_record_id,created_by)
            VALUES (:room,:package,:start,:end,:end,:start,:occupants,:months,:price,'OPENING',:draft,:manager)
            RETURNING id
        '''), params)
        responsible = max((o for o in record.occupancies if o.resident_id == record.responsible_resident_id),
                          key=lambda o: (o.state == 'STAYING', o.entered_on))
        for occupancy in record.occupancies:
            occupancy_id = db.scalar(text('''
                INSERT INTO kamartha.occupancies(lease_id,resident_id,entered_on,state,exited_on,exit_date_unknown,recorded_by)
                VALUES (:lease,:resident,:entered,:state,:exited,:unknown,:manager) RETURNING id
            '''), {'lease': lease, 'resident': occupancy.resident_id, 'entered': occupancy.entered_on,
                   'state': occupancy.state, 'exited': occupancy.exited_on, 'unknown': occupancy.exit_date_unknown,
                   'manager': manager_id})
            if occupancy is responsible:
                # Administrative closure time, not an invented historical exit date.
                db.execute(text('''
                    INSERT INTO kamartha.responsible_history(lease_id,occupancy_id,reason,actor_id,valid_until)
                    VALUES (:lease,:occupancy,'Penanggung jawab data awal',:manager,
                            CASE WHEN :staying THEN NULL ELSE clock_timestamp() END)
                '''), {'lease': lease, 'occupancy': occupancy_id, 'manager': manager_id,
                       'staying': occupancy.state == 'STAYING'})
        for invoice in record.invoices:
            months = (invoice.period_start.year - record.starts_on.year) * 12 + invoice.period_start.month - record.starts_on.month
            end = period_boundary(record.starts_on, package['period_months'], months // package['period_months'] + 1)
            db.execute(text('''
                INSERT INTO kamartha.invoices(lease_id,period_start,period_end,due_on,amount,opening_paid,source,initialization_record_id)
                VALUES (:lease,:start,:end,:due,:amount,:paid,'OPENING',:draft)
            '''), {'lease': lease, 'start': invoice.period_start, 'end': end, 'due': invoice.due_on,
                   'amount': invoice.amount, 'paid': invoice.opening_paid, 'draft': draft['id']})
        db.execute(text("UPDATE kamartha.initialization_records SET state='FINALIZED', validation_errors='[]'::jsonb WHERE id=:id"), {'id': draft['id']})


def encode_draft(data):
    try:
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AppError('DRAFT_INVALID', 'Berkas harus berisi nilai JSON yang sah.', 422) from exc
    if len(encoded.encode()) > 262144:
        raise AppError('DRAFT_TOO_LARGE', 'Berkas data awal terlalu besar.', 422)
    return encoded
