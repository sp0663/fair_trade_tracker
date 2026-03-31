-- Custom query to trace the flow of a specific batch through the supply chain, showing all related batches that are derived from it

WITH RECURSIVE trace AS (
    SELECT
        b.id,
        b.product_name
    FROM
        batches b
    WHERE
        b.id = 1 -- Replace with the batch ID you want to trace

    UNION

    SELECT
        child.id,
        child.product_name
    FROM batches child
    JOIN batch_relations br
        ON br.child_batch_id = child.id
    JOIN trace t
        ON t.id = br.parent_batch_id
)

SELECT * FROM trace;