-- Preserve every customer and aggregate only transactions with a matching key.
CREATE TABLE reconciled_customers AS
SELECT
    c.customer_id,
    c.customer_name,
    COUNT(t.transaction_id) AS transaction_count,
    ROUND(COALESCE(SUM(t.amount), 0), 2) AS total_amount
FROM source_customers AS c
LEFT JOIN normalized_transactions AS t
    ON t.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name;

-- Keep join exceptions visible as a deliverable rather than only counting them.
CREATE TABLE unmatched_transactions AS
SELECT
    t.transaction_id,
    t.customer_id,
    t.amount
FROM normalized_transactions AS t
LEFT JOIN source_customers AS c
    ON c.customer_id = t.customer_id
WHERE c.customer_id IS NULL;
