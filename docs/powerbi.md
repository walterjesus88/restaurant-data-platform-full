# Power BI — Restaurant Data Platform

## Conexión a BigQuery

1. Abre Power BI Desktop
2. **Obtener datos** → **Google BigQuery** (o Azure / SQL Server si usas el conector)
3. Inicia sesión con tu cuenta de Google (la misma del proyecto `realtime-sales-pipeline`)
4. Selecciona el proyecto y dataset `sales_analytics`

## Importar las vistas como tablas

Marca estas vistas para importar:

| Vista | Contenido |
|-------|-----------|
| `vw_sales_daily` | Ventas agregadas por tienda y día |
| `vw_top_products` | Ranking de productos más vendidos |
| `vw_ticket_promedio` | Ticket promedio por tienda |
| `vw_delivery_summary` | Resumen de pedidos delivery |
| `vw_inventory_current` | Stock actual por tienda y producto |
| `vw_consolidado` | Vista unificada ventas + delivery |

## Modelo en Power BI (opcional)

Las vistas ya vienen pre-agregadas, pero si quieres un modelo tipo estrella:

1. Importa las tablas del star schema directamente:
   - `dim_store`
   - `dim_product`
   - `dim_date`
   - `fact_sales`
2. **Relaciones**:
   - `fact_sales[store_id]` → `dim_store[store_id]` (Muchos:1)
   - `fact_sales[product_id]` → `dim_product[product_id]` (Muchos:1)
   - `fact_sales[date_id]` → `dim_date[date_id]` (Muchos:1)

## Visualizaciones sugeridas

### Página 1 — Resumen Ejecutivo

| Visual | Campo/Vista |
|--------|------------|
| **Tarjeta** — Venta total hoy | `vw_consolidado[venta_total]` |
| **Tarjeta** — Delivery pedidos hoy | `vw_consolidado[delivery_pedidos]` |
| **Gráfico de líneas** — Ventas últimos 30 días | `vw_sales_daily[fecha]`, `[venta_total]` |
| **Tabla** — Top 10 productos | `vw_top_products[producto]`, `[total_vendido]`, `[ingreso_total]` |
| **Segmentación** — Fecha (range) | `vw_sales_daily[fecha]` |

### Página 2 — Ventas por Tienda

| Visual | Campos |
|--------|--------|
| **Gráfico de barras** — Venta total por tienda | `vw_sales_daily[tienda]`, `[venta_total]` |
| **Gráfico de columnas** — Ticket promedio | `vw_ticket_promedio[tienda]`, `[ticket_promedio]` |
| **Tabla** — Detalle diario | `vw_sales_daily[fecha]`, `[tienda]`, `[venta_total]`, `[transacciones]`, `[ticket_promedio]` |
| **Segmentación** — Tienda | `vw_sales_daily[tienda]` |

### Página 3 — Delivery

| Visual | Campos |
|--------|--------|
| **Gráfico de barras apiladas** — Pedidos por estado y fecha | `vw_delivery_summary[fecha]`, `[pedidos]`, `[estado]` |
| **Tarjeta** — Monto total delivery | `vw_delivery_summary[monto_total]` |
| **Tarjeta** — Monto promedio | `vw_delivery_summary[monto_promedio]` |

### Página 4 — Inventario

| Visual | Campos |
|--------|--------|
| **Tabla** — Stock actual por tienda y producto | `vw_inventory_current[tienda]`, `[producto]`, `[stock]` |
| **Gráfico de barras** — Productos con menor stock | `vw_inventory_current[producto]`, `[stock]` |
| **Segmentación** — Tienda | `vw_inventory_current[tienda]` |

### Página 5 — Consolidado

| Visual | Campos |
|--------|--------|
| **Gráfico de líneas** — Ventas vs Delivery | `vw_consolidado[fecha]`, `[venta_total]`, `[delivery_monto]` |
| **Tabla** — Detalle consolidado | Todas las columnas de `vw_consolidado` |

## Medidas DAX recomendadas

Crea estas medidas si usas el modelo estrella (`fact_sales` + dimensiones):

```dax
Venta Total = SUM(fact_sales[total_amount])

Transacciones = COUNTROWS(fact_sales)

Ticket Promedio = DIVIDE([Venta Total], [Transacciones])

Cantidad Vendida = SUM(fact_sales[quantity])

Venta vs Promedio =
VAR venta_actual = [Venta Total]
VAR promedio_general =
    CALCULATE([Venta Total], ALL(dim_store))
RETURN
    DIVIDE(venta_actual - promedio_general, promedio_general)
```

## Refrescar datos

- **Batch**: el DAG de Composer corre a diario y actualiza todas las tablas y vistas
- **Streaming**: los datos de delivery llegan en tiempo real
- **Power BI**: configura Actualización programada en Power BI Service (General Settings → Scheduled refresh)
- O usa DirectQuery en lugar de Import para ver datos siempre actualizados (recomendado si hay volumen alto)

## Publicar

1. **Guardar** el `.pbix`
2. **Publicar** → Power BI Service (el workspace que prefieras)
3. Configurar credenciales de BigQuery en **Configuración del dataset** → **Credenciales de origen de datos**
