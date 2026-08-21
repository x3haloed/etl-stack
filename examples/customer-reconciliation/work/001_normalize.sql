-- Interpret source values without altering the source tables.
CREATE TABLE normalized_transactions AS
SELECT
    TRIM(transaction_id) AS transaction_id,
    UPPER(TRIM(customer_id)) AS customer_id,
    CAST(amount AS NUMERIC) AS amount
FROM source_transactions;
