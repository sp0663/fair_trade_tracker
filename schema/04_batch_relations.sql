-- This table defines the relationships between batches, allowing us to track the flow of products through the supply chain

CREATE TABLE batch_relations (
    parent_batch_id INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    child_batch_id INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_batch_id, child_batch_id),
    CHECK (parent_batch_id <> child_batch_id)
);