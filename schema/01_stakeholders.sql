-- This file defines the "stakeholders" table, which represents the various participants in the supply chain

CREATE TABLE stakeholders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'processor', 'distributor', 'retailer')),
    certification_status BOOLEAN NOT NULL DEFAULT FALSE,
    certification_expiry DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);