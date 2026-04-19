-- Fair Trade Supply Chain Tracker — Ad-hoc Test Queries
-- These snippets exercise each subsystem. They are intended to be run one at
-- a time (e.g. from psql or pgAdmin) to confirm the DB behaves as expected
-- after loading setup/setup.sql and seed/seed_data.sql.

-- ─── SCHEMA SANITY ──────────────────────────────────────────────────────────

-- All tables present.
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- All triggers installed.
SELECT trigger_name, event_manipulation, event_object_table, action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, action_timing;

-- All user-defined stored functions (excluding trigger bodies).
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
  AND routine_name NOT IN (
      'check_certification','check_transfer_certification',
      'log_batch_insert','log_batch_update','prevent_audit_modification'
  )
ORDER BY routine_name;


-- ─── CERTIFICATION TRIGGER (BEFORE INSERT) ──────────────────────────────────

-- 1. NO CERTIFICATION (stakeholder 17). Should RAISE EXCEPTION.
-- INSERT INTO batches (product_name, quantity, unit, current_owner_id)
-- VALUES ('Illegal Batch', 100, 'kg', 17);

-- 2. EXPIRED certification (stakeholder 16, expiry 2020-01-01). Should RAISE EXCEPTION.
-- INSERT INTO batches (product_name, quantity, unit, current_owner_id)
-- VALUES ('Expired Cert Batch', 100, 'kg', 16);

-- 3. REVOKED certification (stakeholder 18, is_active = FALSE). Should RAISE EXCEPTION.
-- INSERT INTO batches (product_name, quantity, unit, current_owner_id)
-- VALUES ('Revoked Cert Batch', 100, 'kg', 18);


-- ─── TRANSFER TRIGGER (BEFORE UPDATE) ───────────────────────────────────────

-- 4. Transfer to an uncertified owner. Should RAISE EXCEPTION.
-- UPDATE batches SET current_owner_id = 17 WHERE id = 107;

-- 5. Legal transfer through the stored function. Returns a confirmation string.
-- SELECT transfer_batch(106, 4);
-- SELECT transfer_batch(106, 5);   -- transfer back for a clean state


-- ─── AUDIT IMMUTABILITY ─────────────────────────────────────────────────────

-- 6. Any UPDATE on audit_log must be rejected.
-- UPDATE audit_log SET action = 'hacked' WHERE id = 1;

-- 7. Any DELETE on audit_log must be rejected.
-- DELETE FROM audit_log WHERE id = 1;


-- ─── RECURSIVE LINEAGE ──────────────────────────────────────────────────────

-- 8. Backward lineage of a final retail batch (should return 4 depth levels, 0..3).
SELECT * FROM get_backward_lineage(106);

-- 9. Forward trace from a raw farm batch (should return every downstream product).
SELECT * FROM get_forward_trace(200);


-- ─── VIEWS ──────────────────────────────────────────────────────────────────

-- 10. All four compliance states should appear.
SELECT compliance_status, COUNT(*) AS n
FROM v_compliance_overview
GROUP BY compliance_status
ORDER BY compliance_status;

-- 11. Three supply chains, 8 batches each.
SELECT * FROM v_supply_chain_summary ORDER BY supply_chain;

-- 12. 6 leaf nodes and 6 root nodes (2 farms × 3 chains).
SELECT 'leaf'  AS kind, COUNT(*) FROM v_final_products
UNION ALL
SELECT 'root'  AS kind, COUNT(*) FROM v_raw_materials;


-- ─── ANALYTICS ──────────────────────────────────────────────────────────────

-- 13. Branching factor per batch.
SELECT b.id, b.product_name, COUNT(br.child_batch_id) AS children
FROM batches b
LEFT JOIN batch_relations br ON b.id = br.parent_batch_id
GROUP BY b.id, b.product_name
ORDER BY children DESC, b.id;

-- 14. Maximum supply-chain depth from each root. Expected depth = 3 on every chain.
WITH RECURSIVE chain AS (
    SELECT b.id AS root_id, b.product_name AS root_product, b.id, 0 AS depth
    FROM batches b
    WHERE b.id NOT IN (SELECT child_batch_id FROM batch_relations)
    UNION ALL
    SELECT c.root_id, c.root_product, br.child_batch_id, c.depth + 1
    FROM chain c
    JOIN batch_relations br ON br.parent_batch_id = c.id
)
SELECT root_id, root_product, MAX(depth) AS max_chain_depth
FROM chain
GROUP BY root_id, root_product
ORDER BY root_id;
