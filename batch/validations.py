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

        if isinstance(record[field], str) and record[field].strip() == "":
            return False

    try:
        cantidad = int(record["cantidad"])
        total = float(record["total"])
    except (ValueError, TypeError):
        return False

    if cantidad <= 0:
        return False

    if total < 0:
        return False

    return True