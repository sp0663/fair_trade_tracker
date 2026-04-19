BEGIN;

-- Clear existing data
DROP TABLE IF EXISTS stakeholders CASCADE;
DROP TABLE IF EXISTS batches CASCADE;
DROP TABLE IF EXISTS certifications CASCADE;  
DROP TABLE IF EXISTS batch_relations CASCADE;
DROP TABLE IF EXISTS audit_log CASCADE;

-- Create stakeholders table
CREATE TABLE stakeholders (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('farmer', 'processor', 'distributor', 'retailer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create batches table
CREATE TABLE batches (
    id SERIAL PRIMARY KEY,
    product_name TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL,
    current_owner_id INT NOT NULL REFERENCES stakeholders(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create certifications table
CREATE TABLE certifications (
    id SERIAL PRIMARY KEY,
    stakeholder_id INT REFERENCES stakeholders(id),
    certifying_body TEXT NOT NULL,  
    issue_date DATE NOT NULL,
    expiry_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create batch_relations table
CREATE TABLE batch_relations (
    parent_batch_id INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    child_batch_id INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_batch_id, child_batch_id),
    CHECK (parent_batch_id <> child_batch_id)
);

-- Create audit_log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    batch_id INT NOT NULL REFERENCES batches(id),
    action TEXT NOT NULL CHECK (action IN ('created', 'updated', 'transferred')),
    actor_id INT NOT NULL REFERENCES stakeholders(id),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create View
CREATE OR REPLACE VIEW v_batch_details AS
SELECT b.id AS batch_id,
       b.product_name,
       b.quantity,
       b.unit,
       s.name AS owner_name,
       s.role AS owner_role,
       (EXISTS (
           SELECT 1 FROM certifications c 
           WHERE c.stakeholder_id = s.id 
             AND c.is_active = TRUE 
             AND (c.expiry_date IS NULL OR c.expiry_date > CURRENT_DATE)
       )) AS certification_status,
       b.created_at
FROM batches b
JOIN stakeholders s ON b.current_owner_id = s.id;

-- Certification Trigger
CREATE OR REPLACE FUNCTION check_certification()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM certifications
        WHERE stakeholder_id = NEW.current_owner_id
        AND is_active = TRUE
        AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
    ) THEN
        RAISE EXCEPTION 'Stakeholder is not certified or certification expired';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Audit Log Trigger
CREATE OR REPLACE FUNCTION log_batch_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (batch_id, action, actor_id)
    VALUES (NEW.id, 'created', NEW.current_owner_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER certification_trigger
BEFORE INSERT ON batches
FOR EACH ROW
EXECUTE FUNCTION check_certification();

CREATE TRIGGER audit_insert_trigger
AFTER INSERT ON batches
FOR EACH ROW
EXECUTE FUNCTION log_batch_insert();

COMMIT;