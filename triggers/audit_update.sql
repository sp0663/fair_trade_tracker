
-- Automatically logs ownership transfers and general updates to the batches table.
CREATE OR REPLACE FUNCTION log_batch_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.current_owner_id <> NEW.current_owner_id THEN
        -- Ownership transfer
        INSERT INTO audit_log (batch_id, action, actor_id)
        VALUES (NEW.id, 'transferred', NEW.current_owner_id);
    ELSE
        -- General update (quantity, product_name, etc.)
        INSERT INTO audit_log (batch_id, action, actor_id)
        VALUES (NEW.id, 'updated', NEW.current_owner_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_update_trigger
AFTER UPDATE ON batches
FOR EACH ROW
EXECUTE FUNCTION log_batch_update();
