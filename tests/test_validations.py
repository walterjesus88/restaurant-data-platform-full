from batch.validations import validate_record

def test_negative_amount():

    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": -100
    }

    assert validate_record(record) is False


def test_valid_record():

    record = {
        "fecha": "2026-05-01",
        "tienda": "Miraflores",
        "producto": "Hamburguesa",
        "cantidad": 1,
        "total": 100
    }

    assert validate_record(record) is True