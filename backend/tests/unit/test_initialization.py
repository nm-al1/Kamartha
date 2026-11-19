from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.initialization.rules import validate_record, overlaps
from app.modules.initialization.schemas import OpeningRecord
from app.modules.rooms.schemas import RoomInput
from app.modules.initialization.service import encode_draft
from app.core.errors import AppError


def example():
    resident = str(uuid4())
    return {
        'room_id': str(uuid4()), 'package_id': str(uuid4()),
        'starts_on': '2026-01-31', 'ends_on': '2026-03-31', 'price': 500000,
        'responsible_resident_id': resident,
        'occupancies': [{'resident_id': resident, 'entered_on': '2026-01-31', 'state': 'STAYING'}],
        'invoices': [{'period_start': '2026-02-28', 'due_on': '2026-02-28', 'amount': 500000, 'opening_paid': 500000}],
    }


def validate(data):
    return validate_record(OpeningRecord.model_validate(data), cutover=date(2026, 3, 1),
                           today=date(2026, 3, 1), occupant_type=1, period_months=1, capacity=2)


def test_paid_current_period_is_required_and_keeps_original_anchor():
    assert validate(example()) == []
    data = example()
    data['invoices'] = []
    assert validate(data)


@pytest.mark.parametrize('distinct', [False, True])
def test_two_initial_residents_must_be_distinct_even_with_empty_intervals(distinct):
    data = example()
    first = {**data['occupancies'][0], 'state': 'EXITED', 'exited_on': data['starts_on']}
    second = {**first, 'resident_id': str(uuid4()) if distinct else first['resident_id']}
    data['occupancies'] = [first, second]
    errors = validate_record(OpeningRecord.model_validate(data), cutover=date(2026, 3, 1),
                             today=date(2026, 3, 1), occupant_type=2, period_months=1, capacity=2)
    assert bool(errors) is (not distinct)


def test_ranges_are_half_open():
    assert not overlaps(date(2026, 1, 1), date(2026, 2, 1), date(2026, 2, 1), None)
    assert overlaps(date(2026, 1, 1), None, date(2026, 2, 1), date(2026, 3, 1))
    assert not overlaps(date(2026, 2, 1), date(2026, 2, 1), date(2026, 1, 1), None)


@pytest.mark.parametrize('mutation', ['overpaid', 'duplicate', 'bad_end', 'wrong_price', 'future_exit', 'bad_responsible'])
def test_invalid_opening_records(mutation):
    data = example()
    if mutation == 'overpaid': data['invoices'][0]['opening_paid'] = 500001
    if mutation == 'duplicate': data['invoices'] *= 2
    if mutation == 'bad_end': data['ends_on'] = '2026-03-30'
    if mutation == 'wrong_price': data['invoices'][0]['amount'] = 400000
    if mutation == 'future_exit': data['occupancies'][0].update(state='EXITED', exited_on='2026-04-01')
    if mutation == 'bad_responsible': data['responsible_resident_id'] = str(uuid4())
    assert validate(data)


def test_room_rejects_fractional_money_and_blank_number():
    for values in [dict(number=' ', reference_price=100), dict(number='A1', reference_price=1.5)]:
        with pytest.raises(ValidationError):
            RoomInput(room_type='Standar', supported_occupants=2, **values)


@pytest.mark.parametrize('mutation', ['bad_start', 'bad_enter', 'still_has_exit', 'exit_missing', 'duplicate_person', 'extra_person', 'future_period'])
def test_opening_occupancy_boundaries(mutation):
    data = example()
    if mutation == 'bad_start': data['starts_on'] = '2026-03-02'
    if mutation == 'bad_enter': data['occupancies'][0]['entered_on'] = '2026-01-01'
    if mutation == 'still_has_exit': data['occupancies'][0]['exited_on'] = '2026-02-20'
    if mutation == 'exit_missing': data['occupancies'][0]['state'] = 'EXITED'
    if mutation == 'duplicate_person': data['occupancies'] *= 2
    if mutation == 'extra_person': data['occupancies'].append({**data['occupancies'][0], 'resident_id': str(uuid4())})
    if mutation == 'future_period': data['invoices'][0]['period_start'] = '2026-03-31'
    assert validate(data)


@pytest.mark.parametrize('data', [{'amount': float('nan')}, {'notes': 'a' * 262145}])
def test_draft_rejects_nonfinite_and_oversized_values(data):
    with pytest.raises(AppError) as error:
        encode_draft(data)
    assert error.value.status == 422
