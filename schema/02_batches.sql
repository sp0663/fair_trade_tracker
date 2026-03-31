CREATE TABLE batches (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL,
    current_owner_id INT NOT NULL REFERENCES stakeholders(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);