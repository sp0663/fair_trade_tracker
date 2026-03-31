CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    batch_id INT NOT NULL REFERENCES batches(id),
    action TEXT NOT NULL CHECK (action IN ('created', 'updated', 'transferred')),
    actor_id INT NOT NULL REFERENCES stakeholders(id),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);