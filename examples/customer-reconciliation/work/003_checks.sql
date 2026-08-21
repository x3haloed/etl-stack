-- Encode task-specific failure modes as reviewable data.
CREATE TABLE checks (
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    observed TEXT NOT NULL,
    expected TEXT NOT NULL
);

INSERT INTO checks
SELECT
    'duplicate_customer_ids',
    CASE WHEN COUNT(*) = 0 THEN 'pass' ELSE 'fail' END,
    CAST(COUNT(*) AS TEXT),
    '0'
FROM (
    SELECT customer_id
    FROM source_customers
    GROUP BY customer_id
    HAVING COUNT(*) > 1
);

INSERT INTO checks
SELECT
    'unmatched_transaction_rows',
    CASE WHEN COUNT(*) = 1 THEN 'pass' ELSE 'fail' END,
    CAST(COUNT(*) AS TEXT),
    '1 known exception'
FROM unmatched_transactions;

INSERT INTO checks
SELECT
    'matched_amount_control_total',
    CASE WHEN ROUND(COALESCE(SUM(t.amount), 0), 2) = 450.00 THEN 'pass' ELSE 'fail' END,
    printf('%.2f', ROUND(COALESCE(SUM(t.amount), 0), 2)),
    '450.00'
FROM normalized_transactions AS t
INNER JOIN source_customers AS c
    ON c.customer_id = t.customer_id;
