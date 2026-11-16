-- Revision 001_people_groups_expansion
-- Adds columns and indexes to tables that already exist.
-- New tables are created from the SQLAlchemy models by the same revision.
-- Every statement is safe to run again. Nothing is dropped.

ALTER TABLE people ADD COLUMN IF NOT EXISTS preferred_name VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS middle_name VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS title VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS biography TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS preferred_contact_method VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS contact_preferences TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS membership_status VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS member_since DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS date_first_attended DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS baptism_status VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS baptism_date DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS baptism_location VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS confirmation_date DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS previous_church VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS membership_transfer_notes TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS date_joined DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS date_membership_ended DATE NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS reason_for_leaving TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS ministry_involvement TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS pastoral_notes TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS school_grade VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS school_name VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS occupation VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS employer VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS nationality VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS preferred_language VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS timezone VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS volunteer_status VARCHAR NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS skills TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS interests TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS allergies TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS special_requirements TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS emergency_notes TEXT NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NULL;
ALTER TABLE people ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NULL;

ALTER TABLE addresses ADD COLUMN IF NOT EXISTS unit VARCHAR NULL;
ALTER TABLE people_addresses ADD COLUMN IF NOT EXISTS is_primary BOOLEAN NULL;

ALTER TABLE households ADD COLUMN IF NOT EXISTS name VARCHAR NULL;
ALTER TABLE households ADD COLUMN IF NOT EXISTS notes TEXT NULL;
ALTER TABLE households ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NULL;
ALTER TABLE households ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS ix_people_last_first ON people (last_name, first_name);
CREATE INDEX IF NOT EXISTS ix_people_email ON people (email);
CREATE INDEX IF NOT EXISTS ix_people_mobile ON people (mobile_number);
CREATE INDEX IF NOT EXISTS ix_people_preferred_name ON people (preferred_name);
CREATE INDEX IF NOT EXISTS ix_people_lifecycle ON people (lifecycle_status);
CREATE INDEX IF NOT EXISTS ix_people_membership_status ON people (membership_status);
CREATE INDEX IF NOT EXISTS ix_people_dob ON people (date_of_birth);
CREATE INDEX IF NOT EXISTS ix_people_gender ON people (gender);
CREATE INDEX IF NOT EXISTS ix_people_marital_status ON people (marital_status);
CREATE INDEX IF NOT EXISTS ix_addresses_city_suburb ON addresses (city, suburb);
CREATE INDEX IF NOT EXISTS ix_addresses_postal_code ON addresses (postal_code);
CREATE INDEX IF NOT EXISTS ix_households_leader ON households (leader_id);
CREATE INDEX IF NOT EXISTS ix_household_people_household ON household_people (household_id);
CREATE INDEX IF NOT EXISTS ix_household_people_person ON household_people (person_id);
CREATE INDEX IF NOT EXISTS ix_people_addresses_person_address ON people_addresses (person_id, address_id);
CREATE INDEX IF NOT EXISTS ix_people_addresses_address ON people_addresses (address_id);
