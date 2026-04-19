-- Fair Trade Supply Chain Tracker — Full DB Bootstrap
-- Drops and re-creates every object: tables, triggers, views, functions.
-- Run this file first, then seed/seed_data.sql to populate sample data.

BEGIN;

-- ─── Clear existing objects (CASCADE drops dependent views/triggers) ───
DROP TABLE IF EXISTS audit_log       CASCADE;
DROP TABLE IF EXISTS batch_relations CASCADE;
DROP TABLE IF EXISTS certifications  CASCADE;
DROP TABLE IF EXISTS batches         CASCADE;
DROP TABLE IF EXISTS stakeholders    CASCADE;

-- Drop any prior stored-function signatures so that a RETURN type change does
-- not collide with CREATE OR REPLACE.
DROP FUNCTION IF EXISTS transfer_batch(INT, INT)           CASCADE;
DROP FUNCTION IF EXISTS get_backward_lineage(INT)          CASCADE;
DROP FUNCTION IF EXISTS get_forward_trace(INT)             CASCADE;
DROP FUNCTION IF EXISTS get_compliance_report()            CASCADE;
DROP FUNCTION IF EXISTS check_certification()              CASCADE;
DROP FUNCTION IF EXISTS check_transfer_certification()     CASCADE;
DROP FUNCTION IF EXISTS log_batch_insert()                 CASCADE;
DROP FUNCTION IF EXISTS log_batch_update()                 CASCADE;
DROP FUNCTION IF EXISTS prevent_audit_modification()       CASCADE;


-- Participants in the supply chain (farmer, processor, distributor, retailer).
CREATE TABLE stakeholders (
    id         SERIAL PRIMARY KEY,
    name       TEXT NOT NULL,
    role       TEXT NOT NULL CHECK (role IN ('farmer', 'processor', 'distributor', 'retailer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual product batches flowing through the supply chain.
CREATE TABLE batches (
    id               SERIAL PRIMARY KEY,
    product_name     TEXT NOT NULL,
    quantity         INT  NOT NULL CHECK (quantity > 0),
    unit             TEXT NOT NULL,
    current_owner_id INT  NOT NULL REFERENCES stakeholders(id),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Certifications held by stakeholders (Fair Trade, Organic, …).
CREATE TABLE certifications (
    id              SERIAL PRIMARY KEY,
    stakeholder_id  INT  REFERENCES stakeholders(id),
    certifying_body TEXT NOT NULL,
    issue_date      DATE NOT NULL,
    expiry_date     DATE,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Many-to-many parent/child edges between batches — models the supply-chain DAG.
CREATE TABLE batch_relations (
    parent_batch_id INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    child_batch_id  INT NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_batch_id, child_batch_id),
    CHECK (parent_batch_id <> child_batch_id)
);

-- Append-only audit ledger.
CREATE TABLE audit_log (
    id         SERIAL PRIMARY KEY,
    batch_id   INT  NOT NULL REFERENCES batches(id),
    action     TEXT NOT NULL CHECK (action IN ('created', 'updated', 'transferred')),
    actor_id   INT  NOT NULL REFERENCES stakeholders(id),
    timestamp  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Rejects batch INSERTs whose owner has no valid, active certification.
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

-- Verifies that the receiving stakeholder has a valid certification before allowing a batch transfer.
CREATE OR REPLACE FUNCTION check_transfer_certification()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.current_owner_id <> NEW.current_owner_id THEN
        IF NOT EXISTS (
            SELECT 1 FROM certifications
            WHERE stakeholder_id = NEW.current_owner_id
              AND is_active = TRUE
              AND (expiry_date IS NULL OR expiry_date > CURRENT_DATE)
        ) THEN
            RAISE EXCEPTION 'Transfer denied: receiving stakeholder (id=%) is not certified or certification has expired.', NEW.current_owner_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Logs a 'created' row whenever a new batch is inserted.
CREATE OR REPLACE FUNCTION log_batch_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (batch_id, action, actor_id)
    VALUES (NEW.id, 'created', NEW.current_owner_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Automatically logs ownership transfers and general updates to the batches table.
CREATE OR REPLACE FUNCTION log_batch_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.current_owner_id <> NEW.current_owner_id THEN
        INSERT INTO audit_log (batch_id, action, actor_id)
        VALUES (NEW.id, 'transferred', NEW.current_owner_id);
    ELSE
        INSERT INTO audit_log (batch_id, action, actor_id)
        VALUES (NEW.id, 'updated', NEW.current_owner_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Ensures that audit log records are immutable and cannot be modified or deleted.
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log records are immutable and cannot be modified or deleted.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER certification_trigger
BEFORE INSERT ON batches
FOR EACH ROW EXECUTE FUNCTION check_certification();

CREATE TRIGGER transfer_certification_trigger
BEFORE UPDATE ON batches
FOR EACH ROW EXECUTE FUNCTION check_transfer_certification();

CREATE TRIGGER audit_insert_trigger
AFTER INSERT ON batches
FOR EACH ROW EXECUTE FUNCTION log_batch_insert();

CREATE TRIGGER audit_update_trigger
AFTER UPDATE ON batches
FOR EACH ROW EXECUTE FUNCTION log_batch_update();

CREATE TRIGGER audit_immutability_trigger
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();


-- Retrieves batch details along with their current owner and certification status.
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

-- Provides a summary of the compliance status for all stakeholders.
CREATE OR REPLACE VIEW v_compliance_overview AS
SELECT s.id AS stakeholder_id,
       s.name,
       s.role,
       c.certifying_body,
       c.issue_date,
       c.expiry_date,
       c.is_active,
       CASE
           WHEN c.id IS NULL THEN 'NO CERTIFICATION'
           WHEN c.is_active = FALSE THEN 'REVOKED'
           WHEN c.expiry_date IS NOT NULL AND c.expiry_date < CURRENT_DATE THEN 'EXPIRED'
           ELSE 'COMPLIANT'
       END AS compliance_status
FROM stakeholders s
LEFT JOIN certifications c ON s.id = c.stakeholder_id;

-- Generates a human-readable audit trail combining logs, batches, and stakeholders.
CREATE OR REPLACE VIEW v_audit_trail AS
SELECT al.id AS log_id,
       al.action,
       b.id  AS batch_id,
       b.product_name,
       s.name AS actor_name,
       s.role AS actor_role,
       al.timestamp
FROM audit_log al
JOIN batches      b ON al.batch_id = b.id
JOIN stakeholders s ON al.actor_id = s.id;

-- Aggregates total batches and quantity broken down by supply chain type.
CREATE OR REPLACE VIEW v_supply_chain_summary AS
SELECT CASE
           WHEN b.product_name LIKE 'Coffee%' THEN 'Coffee'
           WHEN b.product_name LIKE 'Cocoa%' OR b.product_name LIKE 'Chocolate%' THEN 'Cocoa'
           WHEN b.product_name LIKE 'Cotton%' OR b.product_name LIKE 'Fabric%' OR b.product_name LIKE 'Clothing%' THEN 'Cotton'
           ELSE 'Other'
       END AS supply_chain,
       COUNT(b.id)                           AS total_batches,
       SUM(b.quantity)                       AS total_quantity,
       COUNT(DISTINCT b.current_owner_id)    AS unique_stakeholders
FROM batches b
GROUP BY supply_chain;

-- Identifies the leaf nodes of the supply chain, representing final retail products.
CREATE OR REPLACE VIEW v_final_products AS
SELECT b.id AS batch_id,
       b.product_name,
       b.quantity || ' ' || b.unit AS amount,
       s.name AS retailer
FROM batches b
JOIN stakeholders s ON b.current_owner_id = s.id
WHERE b.id NOT IN (SELECT parent_batch_id FROM batch_relations);

-- Identifies the root nodes of the supply chain, representing raw materials at the source.
CREATE OR REPLACE VIEW v_raw_materials AS
SELECT b.id AS batch_id,
       b.product_name,
       b.quantity || ' ' || b.unit AS amount,
       s.name AS source_farm
FROM batches b
JOIN stakeholders s ON b.current_owner_id = s.id
WHERE b.id NOT IN (SELECT child_batch_id FROM batch_relations);


-- Transfers a batch to a new owner. Certification is validated automatically by the transfer trigger.
CREATE OR REPLACE FUNCTION transfer_batch(
    p_batch_id INT,
    p_new_owner_id INT
)
RETURNS TEXT AS $$
DECLARE
    v_old_owner TEXT;
    v_new_owner TEXT;
    v_product   TEXT;
BEGIN
    SELECT s.name, b.product_name INTO v_old_owner, v_product
    FROM batches b
    JOIN stakeholders s ON b.current_owner_id = s.id
    WHERE b.id = p_batch_id;

    IF v_old_owner IS NULL THEN
        RAISE EXCEPTION 'Batch % does not exist.', p_batch_id;
    END IF;

    SELECT name INTO v_new_owner FROM stakeholders WHERE id = p_new_owner_id;
    IF v_new_owner IS NULL THEN
        RAISE EXCEPTION 'Stakeholder % does not exist.', p_new_owner_id;
    END IF;

    UPDATE batches SET current_owner_id = p_new_owner_id WHERE id = p_batch_id;

    RETURN FORMAT('Batch "%s" (id=%s) transferred from %s to %s.',
                  v_product, p_batch_id, v_old_owner, v_new_owner);
END;
$$ LANGUAGE plpgsql;

-- Retrieves the complete backward lineage of a batch, tracing it to its raw material origins.
CREATE OR REPLACE FUNCTION get_backward_lineage(p_batch_id INT)
RETURNS TABLE(
    batch_id    INT,
    product_name TEXT,
    owner_name  TEXT,
    owner_role  TEXT,
    depth       INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE lineage AS (
        SELECT b.id, b.product_name, s.name, s.role, 0 AS depth
        FROM batches b
        JOIN stakeholders s ON b.current_owner_id = s.id
        WHERE b.id = p_batch_id

        UNION

        SELECT parent.id, parent.product_name, ps.name, ps.role, l.depth + 1
        FROM batches parent
        JOIN stakeholders ps ON parent.current_owner_id = ps.id
        JOIN batch_relations br ON br.parent_batch_id = parent.id
        JOIN lineage l ON l.id = br.child_batch_id
    )
    SELECT * FROM lineage ORDER BY depth DESC, batch_id;
END;
$$ LANGUAGE plpgsql;

-- Retrieves the forward trace of a batch to identify all affected downstream products.
CREATE OR REPLACE FUNCTION get_forward_trace(p_batch_id INT)
RETURNS TABLE(
    batch_id    INT,
    product_name TEXT,
    owner_name  TEXT,
    owner_role  TEXT,
    depth       INT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE trace AS (
        SELECT b.id, b.product_name, s.name, s.role, 0 AS depth
        FROM batches b
        JOIN stakeholders s ON b.current_owner_id = s.id
        WHERE b.id = p_batch_id

        UNION

        SELECT child.id, child.product_name, cs.name, cs.role, t.depth + 1
        FROM batches child
        JOIN stakeholders cs ON child.current_owner_id = cs.id
        JOIN batch_relations br ON br.child_batch_id = child.id
        JOIN trace t ON t.id = br.parent_batch_id
    )
    SELECT * FROM trace ORDER BY depth, batch_id;
END;
$$ LANGUAGE plpgsql;

-- Generates a compliance report detailing the certification status for all stakeholders.
CREATE OR REPLACE FUNCTION get_compliance_report()
RETURNS TABLE(
    stakeholder_id    INT,
    name              TEXT,
    role              TEXT,
    certifying_body   TEXT,
    issue_date        DATE,
    expiry_date       DATE,
    is_active         BOOLEAN,
    compliance_status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT s.id, s.name, s.role,
           c.certifying_body,
           c.issue_date,
           c.expiry_date,
           c.is_active,
           CASE
               WHEN c.id IS NULL THEN 'NO CERTIFICATION'
               WHEN c.is_active = FALSE THEN 'REVOKED'
               WHEN c.expiry_date IS NOT NULL AND c.expiry_date < CURRENT_DATE THEN 'EXPIRED'
               ELSE 'COMPLIANT'
           END
    FROM stakeholders s
    LEFT JOIN certifications c ON s.id = c.stakeholder_id
    ORDER BY s.id;
END;
$$ LANGUAGE plpgsql;

COMMIT;
