-- This file defines the trigger and function to log batch actions into the audit_log table

CREATE OR REPLACE FUNCTION log_batch_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (batch_id, action, actor_id)
    VALUES (NEW.id, 'created', NEW.current_owner_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log batch insertions
CREATE TRIGGER audit_insert_trigger
AFTER INSERT ON batches
FOR EACH ROW
EXECUTE FUNCTION log_batch_insert();