from datetime import date
from typing import Iterable

from app.modules.billing.rules import MAX_AMOUNT, period_boundary, validate_amount


def contract_end(anchor: date, period_months: int, periods: int) -> date:
    if not 1 <= periods <= 120:
        raise ValueError('Jumlah periode harus antara 1 dan 120.')
    return period_boundary(anchor, period_months, periods)


def validate_new_contract(*, starts_on: date, cutover: date, today: date,
                          price: int, occupant_type: int, period_months: int,
                          capacity: int, resident_ids: Iterable,
                          responsible_resident_id) -> None:
    validate_amount(price)
    if starts_on < cutover:
        raise ValueError('Kontrak operasional tidak boleh dimulai sebelum tanggal pencatatan.')
    if occupant_type not in (1, 2):
        raise ValueError('Jenis hunian harus satu atau dua orang.')
    if period_months not in (1, 6, 12):
        raise ValueError('Periode paket harus 1, 6 atau 12 bulan.')
    if occupant_type > capacity:
        raise ValueError('Kamar tidak mendukung jumlah penghuni pada paket ini.')
    residents = list(resident_ids)
    if len(residents) != occupant_type:
        raise ValueError('Jumlah penghuni harus sama dengan jenis hunian paket.')
    if len(set(residents)) != len(residents):
        raise ValueError('Penghuni dalam satu kontrak harus berbeda.')
    if responsible_resident_id not in residents:
        raise ValueError('Penanggung jawab harus salah satu penghuni kontrak.')


def occupancy_end(occupancy) -> date:
    if occupancy['state'] == 'STAYING':
        return date.max
    if occupancy['state'] == 'CONTINUED':
        return occupancy['continued_on'] or date.max
    if occupancy['exited_on'] is None:
        return date.max
    return occupancy['exited_on']


def intervals_overlap(start, end, other_start, other_end) -> bool:
    return start < other_end and other_start < end


def room_conflict(rows, *, starts_on: date, ends_on: date) -> bool:
    for row in rows:
        end = date.max if row['staying'] else row['effective_ends_on']
        if intervals_overlap(starts_on, ends_on, row['starts_on'], end):
            return True
    return False


def resident_conflict(rows, *, starts_on: date, ends_on: date) -> bool:
    return any(
        intervals_overlap(starts_on, ends_on, row['entered_on'], occupancy_end(row))
        for row in rows
    )


def validate_exit(*, exited_on: date, entered_on: date, today: date) -> None:
    if exited_on < entered_on:
        raise ValueError('Tanggal keluar tidak boleh sebelum tanggal masuk.')
    if exited_on > today:
        raise ValueError('Tanggal keluar tidak boleh di masa depan.')


def replaceable(*, lease_ends_on: date, today: date, entered_on: date,
                occupied_count: int, capacity: int, predecessor_state: str,
                predecessor_exit_unknown: bool) -> None:
    if today >= lease_ends_on:
        raise ValueError('Kontrak sudah berakhir; gunakan kontrak baru.')
    if entered_on > today:
        raise ValueError('Tanggal masuk pengganti tidak boleh di masa depan.')
    if entered_on >= lease_ends_on:
        raise ValueError('Tanggal masuk pengganti harus sebelum akhir kontrak.')
    if predecessor_state != 'EXITED':
        raise ValueError('Penghuni yang digantikan belum tercatat keluar.')
    if predecessor_exit_unknown:
        raise ValueError('Tanggal keluar penghuni lama belum diketahui; verifikasi dahulu.')
    if occupied_count >= capacity:
        raise ValueError('Jumlah penghuni yang masih tinggal sudah penuh.')


def status_of(*, starts_on: date, effective_ends_on: date, today: date) -> str:
    if effective_ends_on <= today:
        return 'ENDED'
    if starts_on > today:
        return 'SCHEDULED'
    return 'ACTIVE'


def next_invoice(anchor: date, period_months: int, price: int) -> dict:
    validate_amount(price)
    return {
        'period_start': anchor,
        'period_end': period_boundary(anchor, period_months, 1),
        'due_on': anchor,
        'amount': price,
    }


def validate_extension(*, periods: int, effective_ends_on: date, today: date) -> None:
    if not 1 <= periods <= 120:
        raise ValueError('Jumlah periode harus antara 1 dan 120.')
    if today >= effective_ends_on:
        raise ValueError('Kontrak sudah berakhir; buat kontrak baru.')


def amount_limit() -> int:
    return MAX_AMOUNT
