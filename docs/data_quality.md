# Calidad de Datos — Restaurant Data Platform

## 1. Reglas de calidad por capa

### Bronze (Staging — datos crudos)

| Tabla | Validación | Dónde | Acción si falla |
|-------|-----------|-------|----------------|
| `sales_staging` | Columnas requeridas no nulas | `load_sales_bucket.py` (dropna) | Fila eliminada |
| `sales_staging` | `total >= 0` | `load_sales_bucket.py` | Fila eliminada |
| `sales_staging` | Sin filas duplicadas exactas | `load_sales_bucket.py` (drop_duplicates) | Duplicado eliminado |
| `inventory_staging` | Columnas requeridas no nulas | `load_inventory_bucket.py` (dropna) | Fila eliminada |
| `inventory_staging` | `stock >= 0` | `load_inventory_bucket.py` | Fila eliminada |
| `inventory_staging` | Sin filas duplicadas exactas | `load_inventory_bucket.py` (drop_duplicates) | Duplicado eliminado |

### Silver (Final — datos curados)

| Tabla | Validación | Dónde | Acción si falla |
|-------|-----------|-------|----------------|
| `sales_final` | No duplica registros con misma (fecha, tienda, producto) | `incremental.sql` (MERGE) | Actualiza cantidad/total si cambió |
| `inventory_final` | No duplica registros con misma (fecha, tienda, producto) | `incremental_inventory.sql` (MERGE) | Actualiza stock si cambió |
| `delivery_realtime` | Campos requeridos en POST | `streaming/app.py` | HTTP 400, no se publica |

### Gold (Star Schema — analítica)

| Tabla | Validación | Dónde | Acción si falla |
|-------|-----------|-------|----------------|
| `dim_store` | Solo inserta tiendas nuevas | `populate_star_schema.sql` (WHERE NOT IN) | Ignora existentes |
| `dim_product` | Solo inserta productos nuevos | `populate_star_schema.sql` (WHERE NOT IN) | Ignora existentes |
| `dim_date` | Solo inserta fechas nuevas | `populate_star_schema.sql` (WHERE NOT IN) | Ignora existentes |
| `fact_sales` | Se reconstruye completa (TRUNCATE + INSERT) | `populate_star_schema.sql` | Siempre consistente |
| `fact_inventory` | Se reconstruye completa (TRUNCATE + INSERT) | `populate_star_schema.sql` | Siempre consistente |

## 2. Validación por registro (unitaria)

La función `validate_record()` en `batch/validations.py` valida cada registro individual antes de la carga batch:

```python
def validate_record(record):
    # 1. Campos requeridos existen y no son nulos
    # 2. String vacío es rechazado
    # 3. cantidad > 0
    # 4. total >= 0
    # 5. Conversión a int/float segura (ValueError capturado)
```

**Cobertura de tests** (20 tests en total):

| Test | Escenario |
|------|-----------|
| `test_valid_record` | Record correcto → True |
| `test_valid_zero_total` | Total = 0 (válido) → True |
| `test_valid_extra_fields` | Campos adicionales → True |
| `test_negative_amount` | Total negativo → False |
| `test_negative_cantidad` | Cantidad negativa → False |
| `test_zero_cantidad` | Cantidad = 0 → False |
| `test_missing_field` | Campo faltante → False |
| `test_null_field` | Campo nulo → False |
| `test_empty_string` | String vacío → False |
| `test_string_cantidad` | Cantidad no numérica → False |

## 3. Transformaciones estandarizadas

La función `transform_data()` en `batch/transformations.py` normaliza DataFrames:

1. **Columnas a minúsculas** → uniformidad de esquema
2. **Elimina duplicados exactos** → filas repetidas
3. **Fecha a datetime** → tipo de dato correcto para joins temporales

**Cobertura de tests**:

| Test | Escenario |
|------|-----------|
| `test_columns_lowercased` | Columnas mayúsculas → minúsculas |
| `test_duplicates_removed` | 3 filas (1 duplicada) → 2 filas |
| `test_fecha_converted_to_datetime` | String → datetime64 |
| `test_empty_dataframe` | DataFrame vacío → sin error |
| `test_special_characters_preserved` | Tildes y ñ se conservan |

## 4. Streaming — Validación en Flask

```python
# app.py — validación antes de publicar a Pub/Sub
required_fields = ["pedido_id", "estado", "fecha_evento", "monto"]
for field in required_fields:
    if field not in data:
        return jsonify({"status": "error"}), 400
```

**Cobertura de tests** (con mock de PublisherClient):

| Test | Escenario |
|------|-----------|
| `test_valid_delivery` | POST correcto → 200 |
| `test_missing_pedido_id` | Sin pedido_id → 400 |
| `test_missing_estado` | Sin estado → 400 |
| `test_invalid_json_body` | JSON mal formado → 500 |
| `test_missing_all_fields` | Body vacío → 400 |

## 5. Deduplicación streaming (Dataflow)

El pipeline de Dataflow usa `ReadModifyWriteStateSpec` (stateful DoFn) para descartar mensajes duplicados de Pub/Sub:

```python
# dataflow_runner.py — dedup por pedido_id
seen = seen_ids.read() or set()
if pedido_id not in seen:
    seen.add(pedido_id)
    seen_ids.write(seen)
    yield event  # solo la primera vez
```

Cada `pedido_id` se procesa una sola vez, incluso si Pub/Sub lo entrega múltiples veces.

## 6. Brechas identificadas

| Brecha | Riesgo | Sugerencia |
|--------|--------|------------|
| No hay schema enforce en CSV | Si el CSV cambia de formato, pandas infiere distinto | Agregar `dtypes` explícitos en `pd.read_csv()` |
| No hay alertas de calidad | Si una validación elimina filas, no se notifica | Agregar logging de filas rechazadas vs aceptadas |
| Delivery no valida tipos | `monto` negativo o `estado` null se insertan igual | Agregar `validate_record` para delivery también |
| Sin rangos máximos | Un total de 1,000,000 podría ser error o legítimo | Definir umbrales por negocio |
| `validate_record()` no se usa en bucket scripts | Validaciones inline duplicadas | Refactorizar para usar el módulo compartido |

## 7. Tests ejecutándose

```
pytest tests/ -v
```
