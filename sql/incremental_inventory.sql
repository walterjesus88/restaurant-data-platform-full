MERGE sales_analytics.inventory_final T
USING sales_analytics.inventory_staging S
ON T.fecha = S.fecha
AND T.tienda = S.tienda
AND T.producto = S.producto

-- WHEN MATCHED THEN
-- UPDATE SET
--     stock = S.stock

WHEN NOT MATCHED THEN
INSERT (
    fecha,
    tienda,
    producto,
    stock
)
VALUES (
    S.fecha,
    S.tienda,
    S.producto,
    S.stock
);
