CREATE TABLE stakeholders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'processor', 'distributor', 'retailer')),
    certification_status BOOLEAN NOT NULL DEFAULT FALSE,
    certification_expiry DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);