
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
       b.id AS batch_id,
       b.product_name,
       s.name AS actor_name,
       s.role AS actor_role,
       al.timestamp
FROM audit_log al
JOIN batches b ON al.batch_id = b.id
JOIN stakeholders s ON al.actor_id = s.id;

-- Aggregates total batches and quantity broken down by supply chain type.
CREATE OR REPLACE VIEW v_supply_chain_summary AS
SELECT CASE
           WHEN b.product_name LIKE 'Coffee%' THEN 'Coffee'
           WHEN b.product_name LIKE 'Cocoa%' OR b.product_name LIKE 'Chocolate%' THEN 'Cocoa'
           WHEN b.product_name LIKE 'Cotton%' OR b.product_name LIKE 'Fabric%' OR b.product_name LIKE 'Clothing%' THEN 'Cotton'
           ELSE 'Other'
       END AS supply_chain,
       COUNT(b.id) AS total_batches,
       SUM(b.quantity) AS total_quantity,
       COUNT(DISTINCT b.current_owner_id) AS unique_stakeholders
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
