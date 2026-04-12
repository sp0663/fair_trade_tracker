-- This table captures certifications that stakeholders may have, such as Fair Trade, Organic, etc

CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    stakeholder_id INT REFERENCES stakeholders(id),
    certifying_body TEXT NOT NULL,  
    issue_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);