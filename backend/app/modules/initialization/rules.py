from datetime import date

from app.modules.billing.rules import period_boundary


def overlaps(start, end, other_start, other_end):
    if (end is not None and end <= start) or (other_end is not None and other_end <= other_start):
        return False
    return start < (other_end or date.max) and other_start < (end or date.max)


def occupancy_end(occupancy, lease_end):
    if occupancy.state == 'STAYING':
        return None
    return occupancy.exited_on or lease_end


def validate_record(record, *, cutover, today, occupant_type, period_months, capacity):
    errors = []
    if record.starts_on > cutover or record.ends_on <= record.starts_on:
        return ['Rentang kontrak lama tidak sah.']
    boundaries = {}
    index = 0
    while True:
        try:
            start = period_boundary(record.starts_on, period_months, index)
            if start >= record.ends_on:
                break
            end = period_boundary(record.starts_on, period_months, index + 1)
        except ValueError:
            return ['Rentang kalender tidak sah.']
        boundaries[start] = end
        index += 1
    if not boundaries or list(boundaries.values())[-1] != record.ends_on:
        errors.append('Akhir kontrak harus pada batas periode paket penuh.')
    if occupant_type > capacity:
        errors.append('Paket melebihi dukungan kamar.')
    residents = [o.resident_id for o in record.occupancies]
    if record.responsible_resident_id not in residents:
        errors.append('Penanggung jawab harus termasuk penghuni kontrak.')
    for occupancy in record.occupancies:
        if not record.starts_on <= occupancy.entered_on < record.ends_on or occupancy.entered_on > today:
            errors.append('Tanggal masuk harus berada dalam kontrak dan tidak di masa depan.')
        if occupancy.state == 'STAYING':
            if occupancy.exited_on or occupancy.exit_date_unknown:
                errors.append('Penghuni masih tinggal tidak boleh mempunyai tanggal keluar.')
        elif ((occupancy.exited_on is None) == (not occupancy.exit_date_unknown)):
            errors.append('Penghuni keluar perlu tanggal keluar atau konfirmasi tanggal tidak diketahui.')
        if occupancy.exited_on and not occupancy.entered_on <= occupancy.exited_on <= today:
            errors.append('Tanggal keluar tidak sah atau di masa depan.')
    for i, occupancy in enumerate(record.occupancies):
        for other in record.occupancies[i + 1:]:
            if occupancy.resident_id == other.resident_id and overlaps(
                occupancy.entered_on, occupancy_end(occupancy, record.ends_on),
                other.entered_on, occupancy_end(other, record.ends_on),
            ):
                errors.append('Penghunian orang yang sama bertumpuk.')
    points = sorted({o.entered_on for o in record.occupancies})
    for point in points:
        count = sum(o.entered_on <= point < (occupancy_end(o, record.ends_on) or date.max)
                    for o in record.occupancies)
        if count > occupant_type:
            errors.append('Jumlah penghuni bersamaan melebihi paket.')
            break
    initial_residents = [o.resident_id for o in record.occupancies if o.entered_on == record.starts_on]
    if len(initial_residents) != occupant_type:
        errors.append('Penghunian awal harus sesuai jumlah orang pada paket.')
    if len(set(initial_residents)) != len(initial_residents):
        errors.append('Penghuni awal harus orang yang berbeda.')
    staying = [o.resident_id for o in record.occupancies if o.state == 'STAYING']
    if staying and record.responsible_resident_id not in staying:
        errors.append('Penanggung jawab harus dipilih dari penghuni yang masih tinggal.')
    seen = set()
    for invoice in record.invoices:
        if invoice.period_start in seen:
            errors.append('Periode tagihan ganda.')
        seen.add(invoice.period_start)
        if invoice.period_start not in boundaries or invoice.period_start > cutover:
            errors.append('Periode tagihan tidak sesuai kalender kontrak atau melewati tanggal batas.')
        if invoice.opening_paid > invoice.amount:
            errors.append('Dibayar sebelum pencatatan melebihi nominal tagihan.')
        if invoice.amount != record.price:
            errors.append('Nominal tagihan harus sesuai harga kesepakatan per periode.')
    current = next((start for start, end in boundaries.items() if start <= cutover < end), None)
    if current is not None and current not in seen:
        errors.append('Tagihan periode berjalan wajib dimasukkan, termasuk yang sudah lunas.')
    return list(dict.fromkeys(errors))
