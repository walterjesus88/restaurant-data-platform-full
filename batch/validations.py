def validate_record(record):

    required_fields = [
        "fecha",
        "tienda",
        "producto",
        "cantidad",
        "total"
    ]

    for field in required_fields:
        if field not in record:
            return False

        if record[field] is None:
            return False

    if int(record["cantidad"]) <= 0:
        return False

    if float(record["total"]) < 0:
        return False

    return True