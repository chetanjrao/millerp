-- For single stock id
SELECT bags as stock FROM (
SELECT bags FROM materials_incomingstockentry i WHERE id=2
UNION
SELECT 0 - SUM(o.bags) bags
FROM materials_incomingstockentry i
LEFT OUTER JOIN materials_outgoingstockentry o ON i.id = o.stock_id WHERE o.stock_id=2 GROUP BY o.stock_id
UNION
SELECT 0 - SUM(p.bags) bags
FROM materials_incomingstockentry i
LEFT OUTER JOIN materials_processingsideentry p ON i.id = p.stock_id WHERE p.stock_id=2 GROUP BY p.stock_id) as bags

-- For single category stock id
SELECT id, SUM(bags) as stock FROM (
SELECT id, bags FROM materials_incomingstockentry i WHERE category_id=1 GROUP BY id
UNION
SELECT stock_id, 0 - SUM(o.bags) bags
FROM materials_incomingstockentry i
INNER JOIN materials_outgoingstockentry o ON i.id = o.stock_id GROUP BY o.stock_id
UNION
SELECT stock_id, 0 - SUM(p.bags) bags
FROM materials_incomingstockentry i
INNER JOIN materials_processingsideentry p ON i.id = p.stock_id GROUP BY p.stock_id) as bags GROUP by id

-- For all stocks
SELECT c.name, SUM(bags) as stock FROM (
SELECT category_id, bags FROM materials_incomingstockentry i GROUP BY category_id
UNION
SELECT i.category_id, 0 - SUM(o.bags) bags
FROM materials_incomingstockentry i
LEFT OUTER JOIN materials_outgoingstockentry o ON i.id = o.stock_id GROUP BY o.stock_id, i.category_id
UNION
SELECT i.category_id, 0 - SUM(p.bags) bags
FROM materials_incomingstockentry i
LEFT OUTER JOIN materials_processingsideentry p ON i.id = p.stock_id GROUP BY p.stock_id, i.category_id) as bags INNER JOIN materials_category c ON category_id=c.id WHERE mill_id=1 GROUP by category_id