import pandas as pd
import numpy as np
from batch.transformations import transform_data


def test_columns_lowercased():
    df = pd.DataFrame({
        "Fecha": ["2026-05-01"],
        "Tienda": ["Miraflores"],
        "Producto": ["Hamburguesa"],
        "Cantidad": [2],
        "Total": [50]
    })
    result = transform_data(df)
    assert all(c == c.lower() for c in result.columns)


def test_duplicates_removed():
    df = pd.DataFrame({
        "fecha": ["2026-05-01", "2026-05-01", "2026-05-02"],
        "tienda": ["Miraflores", "Miraflores", "Surco"],
        "producto": ["Hamburguesa", "Hamburguesa", "Pizza"],
        "cantidad": [2, 2, 1],
        "total": [50, 50, 30]
    })
    result = transform_data(df)
    assert len(result) == 2


def test_fecha_converted_to_datetime():
    df = pd.DataFrame({
        "fecha": ["2026-05-01"],
        "tienda": ["Miraflores"],
        "producto": ["Hamburguesa"],
        "cantidad": [2],
        "total": [50]
    })
    result = transform_data(df)
    assert pd.api.types.is_datetime64_any_dtype(result["fecha"])


def test_empty_dataframe():
    df = pd.DataFrame({"fecha": pd.Series(dtype=str)})
    result = transform_data(df)
    assert len(result) == 0


def test_special_characters_preserved():
    df = pd.DataFrame({
        "fecha": ["2026-05-01"],
        "tienda": ["José María"],
        "producto": ["Empanada de carne"],
        "cantidad": [3],
        "total": [45]
    })
    result = transform_data(df)
    assert result["tienda"].iloc[0] == "José María"
    assert result["producto"].iloc[0] == "Empanada de carne"
