# Star Schema — Flujo de datos y relaciones

## 1. Flujo completo: cómo nacen las tablas

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   FUENTE     │     │     STAGING      │     │      FINAL       │     │   STAR SCHEMA     │     │     VISTAS      │
│              │     │   (Bronze)       │     │   (Silver)       │     │     (Gold)        │     │                 │
│              │     │                  │     │                  │     │                   │     │                 │
│ ventas_pos   │────▶│  sales_staging   │────▶│   sales_final    │──┐──│  dim_store        │──┐──│ vw_sales_daily  │
│ .csv         │     │                  │     │                  │  │  │  dim_product      │  │  │ vw_top_products │
│              │     │  (truncate +     │     │  (MERGE idemp.)  │  │  │  dim_date         │  │  │ vw_ticket_prom. │
│ inventario   │────▶│ inventory_       │────▶│ inventory_final  │──┤  │  fact_sales       │──┤  │ vw_inventory_   │
│ .csv         │     │ staging          │     │                  │  │  │                   │  │  │ current          │
│              │     │                  │     │                  │  │  │                   │  │  │                 │
│ Flask POST   │────▶│  Pub/Sub         │────▶│ delivery_realtime│──┘  └───────────────────┘  │  │ vw_delivery_    │
│ /delivery    │     │  (streaming)     │     │  (Dataflow)      │                             │  │ summary         │
│              │     │                  │     │                  │                             │  │                 │
└──────────────┘     └──────────────────┘     └──────────────────┘                             │  │ vw_consolidado │
                                                                                              └──│                 │
                                                                                                 └─────────────────┘
```

## 2. Población del Star Schema

El star schema se construye **exclusivamente desde `sales_final`** en este orden:

```
                     sales_final
                   ┌──────┬──────┬────────┬──────┬──────┐
                   │fecha │tienda│producto│cantid│total │
                   │      │      │        │ ad   │      │
                   └──┬───┴──┬───┴──┬─────┴──┬───┴──┬───┘
                      │      │      │        │      │
     ┌────────────────┘      │      │        └──────┐
     ▼                       │      │               ▼
┌──────────┐                 ▼      ▼          ┌──────────────────┐
│ dim_date │          ┌──────────┐ ┌──────────┐│   fact_sales     │
│          │          │dim_store │ │dim_prod. ││                  │
│ date_id  │◄─────────┤          │ │          ││ sale_id (PK)     │
│ (PK)     │          │ store_id │ │product_id││ store_id (FK)───►│ dim_store
│          │          │ (PK)     │ │ (PK)     ││ product_id (FK)─►│ dim_product
│          │          │ store_   │ │ product_ ││ date_id (FK)────►│ dim_date
│          │          │ name     │ │ name     ││ total_amount     │
│          │          └──────────┘ └──────────┘│ quantity         │
│          │                                   └──────────────────┘
│ (fechas  │
│  con     │
│  ventas) │
└──────────┘

Paso 1: INSERT INTO dim_store  → extrae DISTINCT tienda desde sales_final
Paso 2: INSERT INTO dim_product → extrae DISTINCT producto desde sales_final
Paso 3: INSERT INTO dim_date    → extrae DISTINCT fecha desde sales_final
Paso 4: TRUNCATE + INSERT fact_sales → JOIN sales_final + dim_store + dim_product
```

**Las dimensiones son lentas (SCD tipo 1):** solo insertan lo nuevo (`WHERE NOT IN`).
**La tabla de hechos se trunca y reconstruye completa cada vez** (idempotente).

## 3. Cardinalidades (ER)

```
 dim_store ──1──< fact_sales >──1── dim_product
                │
                │
               1
               │
             dim_date

Relaciones:
  dim_store.store_id ──1:N── fact_sales.store_id
  dim_product.product_id ──1:N── fact_sales.product_id
  dim_date.date_id ──1:N── fact_sales.date_id

Cada fact_sales pertenece a UNA tienda, UN producto, UNA fecha.
Cada tienda aparece en MUCHAS ventas.
Cada producto aparece en MUCHAS ventas.
Cada fecha aparece en MUCHAS ventas.
```

## 4. Cómo las vistas consumen el Star Schema

### vw_sales_daily — Ventas por día

```sql
SELECT f.date_id, st.store_name, SUM(f.total_amount) AS venta_total, ...
FROM fact_sales f
LEFT JOIN dim_store st ON f.store_id = st.store_id
GROUP BY f.date_id, st.store_name
```

**JOIN**: `fact_sales` + `dim_store` (para tener el nombre de tienda)
**Cardinalidad**: 1 fila por (fecha, tienda)

### vw_top_products — Ranking de productos

```sql
SELECT p.product_name, SUM(f.quantity) AS total_vendido, ...
FROM fact_sales f
LEFT JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
```

**JOIN**: `fact_sales` + `dim_product` (para tener el nombre del producto)
**Cardinalidad**: 1 fila por producto

### vw_ticket_promedio — Ticket por tienda

```sql
SELECT st.store_name, ROUND(SUM(f.total_amount)/COUNT(*),2) AS ticket_promedio, ...
FROM fact_sales f
LEFT JOIN dim_store st ON f.store_id = st.store_id
GROUP BY st.store_name
```

**JOIN**: `fact_sales` + `dim_store`
**Cardinalidad**: 1 fila por tienda

### vw_inventory_current — Stock actual

```sql
-- NO usa el star schema, lee directo de inventory_final
SELECT tienda, producto, stock, fecha
FROM inventory_final
QUALIFY ROW_NUMBER() OVER (PARTITION BY tienda, producto ORDER BY fecha DESC) = 1
```

**Origen**: `inventory_final` (tabla silver, sin star schema propio)

### vw_delivery_summary — Resumen delivery

```sql
-- NO usa el star schema, lee directo de delivery_realtime
SELECT DATE(fecha_evento) AS fecha, estado, COUNT(*) AS pedidos, ...
FROM delivery_realtime
GROUP BY DATE(fecha_evento), estado
```

**Origen**: `delivery_realtime` (tabla silver, datos streaming)

### vw_consolidado — Ventas + Delivery

```sql
SELECT COALESCE(s.fecha, d.fecha) AS fecha, s.venta_total, d.delivery_monto, ...
FROM vw_sales_daily s
FULL OUTER JOIN vw_delivery_summary d ON s.fecha = d.fecha
```

**Origen**: combina `vw_sales_daily` (star schema) + `vw_delivery_summary` (delivery)

## 5. Resumen visual final

```
                          SALES PIPELINE
┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
│ ventas_pos │──▶│ sales_staging│──▶│ sales_final  │──▶│ dim_store       │──▶│ vw_sales_daily   │
│   .csv     │   │              │   │              │   │ dim_product     │   │ vw_top_products  │
│            │   │ (trunc+carga)│   │ (MERGE)      │   │ dim_date        │   │ vw_ticket_promed │
│            │   │              │   │              │   │ fact_sales      │   └──────────────────┘
└────────────┘   └──────────────┘   └──────────────┘   └─────────────────┘
                                                                                
                          INVENTORY PIPELINE                                   
┌────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ inventario │──▶│ inventory_staging │──▶│ inventory_final  │──▶│ vw_inventory_   │
│   .csv     │   │                  │   │                  │   │ current          │
└────────────┘   └──────────────────┘   └──────────────────┘   └──────────────────┘

                          STREAMING PIPELINE                                    
┌────────────┐   ┌──────────┐   ┌────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Flask     │──▶│ Pub/Sub  │──▶│  Dataflow  │──▶│ delivery_realtime│──▶│ vw_delivery_sum  │
│ /delivery  │   │          │   │  (dedup)   │   │                  │   │                  │
└────────────┘   └──────────┘   └────────────┘   └──────────────────┘   └──────────────────┘
```
