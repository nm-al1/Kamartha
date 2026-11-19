import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[3] / 'ops' / 'local_demo.py'
spec = importlib.util.spec_from_file_location('local_demo', path)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


@pytest.mark.parametrize('name', ['kamartha_demo', 'kamartha_demo_verify', 'kamartha_demo_20261105'])
def test_demo_database_name_is_explicitly_scoped(name):
    assert demo.validate_database(name) == name


@pytest.mark.parametrize('name', ['kamartha', 'postgres', 'kamartha_test', 'kamartha_demo; DROP DATABASE x', '../demo'])
def test_demo_launcher_rejects_non_demo_database_names(name):
    with pytest.raises(ValueError):
        demo.validate_database(name)


def test_test_database_requires_explicit_permission():
    assert demo.validate_database('kamartha_test', allow_test=True) == 'kamartha_test'
    with pytest.raises(ValueError):
        demo.validate_database('kamartha', allow_test=True)
