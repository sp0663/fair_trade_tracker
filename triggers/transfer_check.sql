
-- Verifies that the receiving stakeholder has a valid certification before allowing a batch transfer.
CREATE OR REPLACE FUNCTION check_transfer_certification()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check when ownership is actually changing
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

CREATE TRIGGER transfer_certification_trigger
BEFORE UPDATE ON batches
FOR EACH ROW
EXECUTE FUNCTION check_transfer_certification();
