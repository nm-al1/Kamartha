import pytest
from pydantic import ValidationError

from app.modules.residents.schemas import ResidentInput


def test_resident_trims_identity_and_name():
    resident = ResidentInput(name=' Andi ', identity_type=' KTP ', identity_number=' 123 ')
    assert resident.name == 'Andi'
    assert resident.identity_number == '123'
    assert resident.whatsapp_number is None


@pytest.mark.parametrize('field', ['name', 'identity_type', 'identity_number'])
def test_resident_rejects_blank_required_fields(field):
    values = dict(name='Andi', identity_type='Kartu pelajar', identity_number='123')
    values[field] = '   '
    with pytest.raises(ValidationError):
        ResidentInput(**values)


def test_identity_does_not_require_nik():
    assert ResidentInput(name='Andi', identity_type='Paspor', identity_number='A123').identity_number == 'A123'
