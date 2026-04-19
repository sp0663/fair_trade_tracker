-- This table represents the various participants in the supply chain

CREATE TABLE stakeholders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'processor', 'distributor', 'retailer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);