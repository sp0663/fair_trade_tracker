-- Trigger to check certification status of stakeholders before inserting a batch

CREATE OR REPLACE FUNCTION check_certification()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM stakeholders
        WHERE id = NEW.current_owner_id
          AND certification_status = TRUE
          AND (certification_expiry IS NULL OR certification_expiry > CURRENT_DATE)
    ) THEN
        RAISE EXCEPTION 'Stakeholder is not certified or certification expired';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger

CREATE TRIGGER certification_trigger
BEFORE INSERT ON batches
FOR EACH ROW
EXECUTE FUNCTION check_certification();