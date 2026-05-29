# Retry e Idempotencia — Estrategias

## Reintentos (Retry)

### Batch (Airflow DAG)

| Escenario | Comportamiento |
|-----------|---------------|
| Falla `load_sales_bucket.py` | El DAG tiene `retries: 1`. Si falla, Airflow lo reintenta automáticamente 1 vez. Si vuelve a fallar, queda en estado `failed`. |
| Falla el MERGE (`incremental.sql`) | Se relanza manualmente desde la UI de Airflow (▶️ Clear task). Como es idempotente, ejecutarlo N veces da el mismo resultado. |
| El CSV en GCS se corrompió | Se sube el CSV corregido al bucket y se relanza el DAG. `load_sales_bucket.py` trunca staging primero, así que arranca limpio. |
| Falla `populate_star_schema.sql` | Se relanza. `fact_sales` se trunca y reconstruye completa. Las dimensiones solo insertan lo nuevo. |

**Composer retry automático**: el worker de Airflow reintenta tareas que fallan por errores transitorios del entorno (timeout, falta de recursos) sin intervención manual.

### Streaming (Dataflow)

| Escenario | Comportamiento |
|-----------|---------------|
| Dataflow falla y se reinicia | Beam gestiona **snapshots periódicos** del estado de dedup y la posición en Pub/Sub. Al reiniciar, retoma desde el último checkpoint sin perder mensajes. |
| Pub/Sub entrega duplicado | La suscripción `delivery-sub` tiene modo **at-least-once**. Dataflow recibe el mismo mensaje dos veces, pero el **Stateful DoFn** lo descarta porque el `pedido_id` ya está en el set de vistos. |
| Flask recibe 500 | El cliente (Insomnia / curl) debe reintentar manualmente. Flask no tiene retry interno. |
| Pub/Sub retención | Los mensajes no acknowledge se retienen hasta **7 días**. Si Dataflow está caído ese tiempo, los mensajes se pierden. |

### CI/CD (GitHub Actions)

Si el CI/CD falla (test que no pasa, error de autenticación GCP), se corrige el código y se hace **push nuevamente a `main`**. La acción se dispara automáticamente con cada push.

---

## Idempotencia

Cada operación del pipeline puede ejecutarse múltiples veces sin duplicar datos ni producir resultados incorrectos.

### Batch — MERGE idempotente

```sql
-- incremental.sql (sales)
MERGE sales_analytics.sales_final T
USING sales_analytics.sales_staging S
ON T.fecha = S.fecha AND T.tienda = S.tienda AND T.producto = S.producto

WHEN MATCHED THEN
    UPDATE SET cantidad = S.cantidad, total = S.total  -- actualiza si cambió

WHEN NOT MATCHED THEN
    INSERT (...) VALUES (...)  -- solo agrega registros nuevos
```

**Ejecutarlo 1 vez** → inserta 5 registros nuevos.
**Ejecutarlo 20 veces** → sigue siendo los mismos 5 registros (los que ya existen se matchean y no se insertan).

### Batch — Truncate staging

```sql
-- load_sales_bucket.py ejecuta esto antes de cargar
TRUNCATE TABLE sales_analytics.sales_staging;
```

Cargar el mismo CSV dos veces siempre da el mismo resultado porque staging arranca vacío cada vez.

### Star schema — Población idempotente

**Dimensiones** (INSERT condicional):

```sql
INSERT INTO sales_analytics.dim_store (store_id, store_name)
SELECT ... FROM sales_final
WHERE tienda NOT IN (SELECT store_name FROM dim_store);
```

Las dimensiones solo insertan valores **nuevos**. Los existentes no se tocan. Ejecutar N veces = mismo resultado.

**Fact tables** (TRUNCATE + INSERT):

```sql
TRUNCATE TABLE sales_analytics.fact_sales;

INSERT INTO sales_analytics.fact_sales (...)
SELECT ... FROM sales_final LEFT JOIN dim_store LEFT JOIN dim_product;
```

`fact_sales` y `fact_inventory` se **truncan y reconstruyen completas** cada vez. Siempre dan el mismo resultado con los mismos datos fuente.

### Streaming — Stateful dedup (ReadModifyWriteStateSpec)

```python
class DeduplicatePedidos(beam.DoFn):
    SEEN_IDS = ReadModifyWriteStateSpec("seen_ids", coders.PickleCoder())

    def process(self, element, seen_ids=beam.DoFn.StateParam(SEEN_IDS)):
        event = json.loads(element)
        pedido_id = event.get("pedido_id")
        seen = seen_ids.read() or set()
        if pedido_id not in seen:
            seen.add(pedido_id)
            seen_ids.write(seen)
            yield event  # solo emite si es la primera vez
```

**Beam Stateful**: mantiene un set de `pedido_id` vistos en la memoria del worker. Si Pub/Sub reenvía un mensaje duplicado, el `pedido_id` ya está en el set y se descarta.

**Worker escala**: cada worker tiene su propio estado de dedup para los `pedido_id` que le asigna Beam. La clave (`pedido_id`) asegura que el mismo id siempre va al mismo worker.

### CI/CD — Deploy idempotente

`gsutil cp` sobreescribe archivos en GCS sin preguntar. Subir los mismos scripts N veces deja siempre los mismos archivos.

---

## Resumen visual

```
Operación              Estrategia                Idempotente?
──────────────────────────────────────────────────────────────
load_sales_bucket.py   Truncate → carga           ✅ Sí
incremental.sql         MERGE WHEN NOT MATCHED     ✅ Sí
populate_star_schema    INSERT WHERE NOT IN       ✅ Sí
populate_fact_sales     TRUNCATE → INSERT          ✅ Sí
Flask POST /delivery   Sin retry                  ❌ No (cliente reintenta)
Dataflow dedup          Stateful DoFn             ✅ Sí
gsutil cp               Sobrescribe               ✅ Sí
```
