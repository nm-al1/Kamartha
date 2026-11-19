from datetime import date

import pytest

from app.modules.leases.rules import (
    contract_end, intervals_overlap, replaceable, resident_conflict,
    room_conflict, status_of,
)


def test_contract_end_uses_anchor_and_clips_month_end():
    assert contract_end(date(2027, 1, 31), 1, 1) == date(2027, 2, 28)
    assert contract_end(date(2027, 1, 31), 1, 2) == date(2027, 3, 31)
    assert contract_end(date(2028, 1, 31), 1, 1) == date(2028, 2, 29)
    assert contract_end(date(2026, 3, 10), 6, 2) == date(2027, 3, 10)


def test_interval_overlap_is_half_open():
    assert intervals_overlap(date(2026, 3, 1), date(2026, 4, 1),
                             date(2026, 3, 31), date(2026, 4, 2))
    assert not intervals_overlap(date(2026, 3, 1), date(2026, 4, 1),
                                 date(2026, 4, 1), date(2026, 5, 1))


def test_future_staying_contract_does_not_block_earlier_interval():
    rows = [{'staying': True, 'starts_on': date(2026, 5, 1),
             'effective_ends_on': date(2026, 6, 1)}]
    assert not room_conflict(rows, starts_on=date(2026, 4, 1),
                             ends_on=date(2026, 5, 1))
    assert room_conflict(rows, starts_on=date(2026, 4, 1),
                         ends_on=date(2026, 5, 2))


def test_room_conflict_keeps_staying_occupancy_blocking_after_lease_end():
    rows = [
        {'staying': False, 'starts_on': date(2026, 1, 1),
         'effective_ends_on': date(2026, 2, 1)},
    ]
    assert not room_conflict(rows, starts_on=date(2026, 3, 1),
                             ends_on=date(2026, 4, 1))
    rows[0]['staying'] = True
    assert room_conflict(rows, starts_on=date(2026, 3, 1),
                         ends_on=date(2026, 4, 1))


def test_resident_conflict_uses_exit_boundary_and_unknown_exit_blocks():
    exited = {'state': 'EXITED', 'exited_on': date(2026, 3, 15),
              'continued_on': None, 'entered_on': date(2026, 2, 1)}
    assert not resident_conflict([exited], starts_on=date(2026, 3, 15),
                                 ends_on=date(2026, 5, 1))
    assert resident_conflict([exited], starts_on=date(2026, 3, 14),
                             ends_on=date(2026, 5, 1))
    unknown = {**exited, 'exited_on': None}
    assert resident_conflict([unknown], starts_on=date(2026, 4, 1),
                             ends_on=date(2026, 5, 1))


def test_replacement_requires_exited_predecessor_and_room_for_one():
    kwargs = dict(lease_ends_on=date(2026, 5, 1), today=date(2026, 3, 20),
                  entered_on=date(2026, 3, 16), occupied_count=1, capacity=2,
                  predecessor_state='EXITED', predecessor_exit_unknown=False)
    replaceable(**kwargs)
    with pytest.raises(ValueError):
        replaceable(**{**kwargs, 'occupied_count': 2})
    with pytest.raises(ValueError):
        replaceable(**{**kwargs, 'predecessor_state': 'STAYING'})
    with pytest.raises(ValueError):
        replaceable(**{**kwargs, 'entered_on': date(2026, 3, 21)})
    with pytest.raises(ValueError):
        replaceable(**{**kwargs, 'entered_on': date(2026, 5, 1)})


def test_contract_status_is_derived_from_business_date():
    assert status_of(starts_on=date(2026, 3, 1),
                     effective_ends_on=date(2026, 4, 1),
                     today=date(2026, 2, 28)) == 'SCHEDULED'
    assert status_of(starts_on=date(2026, 3, 1),
                     effective_ends_on=date(2026, 4, 1),
                     today=date(2026, 3, 20)) == 'ACTIVE'
    assert status_of(starts_on=date(2026, 3, 1),
                     effective_ends_on=date(2026, 4, 1),
                     today=date(2026, 4, 1)) == 'ENDED'
