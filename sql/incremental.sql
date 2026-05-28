MERGE sales_analytics.sales_final T
USING sales_analytics.sales_staging S
ON T.fecha = S.fecha
AND T.tienda = S.tienda
AND T.producto = S.producto

WHEN NOT MATCHED THEN
INSERT (
    fecha,
    tienda,
    producto,
    cantidad,
    total
)
VALUES (
    S.fecha,
    S.tienda,
    S.producto,
    S.cantidad,
    S.total
);