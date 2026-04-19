
-- Transfers a batch to a new owner. Certification is validated automatically by the transfer_check trigger.
CREATE OR REPLACE FUNCTION transfer_batch(
    p_batch_id INT,
    p_new_owner_id INT
)
RETURNS TEXT AS $$
DECLARE
    v_old_owner TEXT;
    v_new_owner TEXT;
    v_product TEXT;
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
    batch_id INT,
    product_name TEXT,
    owner_name TEXT,
    owner_role TEXT,
    depth INT
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
    batch_id INT,
    product_name TEXT,
    owner_name TEXT,
    owner_role TEXT,
    depth INT
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
-- Column shape matches v_compliance_overview so the view and the function are interchangeable.
CREATE OR REPLACE FUNCTION get_compliance_report()
RETURNS TABLE(
    stakeholder_id INT,
    name TEXT,
    role TEXT,
    certifying_body TEXT,
    issue_date DATE,
    expiry_date DATE,
    is_active BOOLEAN,
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
