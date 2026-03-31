-- Custom query to trace the parental lineage of a specific batch through the supply chain, showing all related batches that are predecessors of it

WITH RECURSIVE lineage AS (
    SELECT
        b.id,
        b.product_name
    FROM
        batches b
    WHERE
        b.id = 1 -- Replace with the batch ID you want to trace

    UNION

    SELECT
        parent.id,
        parent.product_name
    FROM batches parent
    JOIN batch_relations br
        ON br.parent_batch_id = parent.id
    JOIN lineage l
        ON l.id = br.child_batch_id
)

SELECT * FROM lineage;