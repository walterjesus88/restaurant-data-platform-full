import pytest
from batch.validations import validate_record


def test_valid_record():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": 100
    }
    assert validate_record(record) is True


def test_valid_zero_total():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": 0
    }
    assert validate_record(record) is True


def test_valid_extra_fields():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 2,
        "total": 50,
        "descuento": 5,
        "nota": "sin cebolla"
    }
    assert validate_record(record) is True


def test_negative_amount():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": -100
    }
    assert validate_record(record) is False


def test_negative_cantidad():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": -1,
        "total": 100
    }
    assert validate_record(record) is False


def test_zero_cantidad():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 0,
        "total": 100
    }
    assert validate_record(record) is False


def test_missing_field():
    record = {
        "fecha": "2026-05-01",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": 100
    }
    assert validate_record(record) is False


def test_null_field():
    record = {
        "fecha": "2026-05-01",
        "tienda": None,
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": 100
    }
    assert validate_record(record) is False


def test_empty_string():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "",
        "cantidad": 1,
        "total": 100
    }
    assert validate_record(record) is False


def test_string_cantidad():
    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": "abc",
        "total": 100
    }
    assert validate_record(record) is False