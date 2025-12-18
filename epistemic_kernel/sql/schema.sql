-- PostgreSQL-first schema reflecting PRISMA-aligned constraints.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS references_v1 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_hash TEXT NOT NULL,
    ingestion_source TEXT NOT NULL CHECK (ingestion_source IN ('PubMed', 'ClinicalTrials.gov')),
    ingestion_query TEXT NOT NULL,
    ingestion_timestamp TIMESTAMPTZ NOT NULL,
    raw_response JSONB NOT NULL,
    title TEXT NOT NULL,
    authors TEXT[] NOT NULL,
    abstract TEXT NOT NULL,
    doi TEXT NOT NULL,
    journal TEXT NOT NULL,
    pub_date DATE NOT NULL,
    locked BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parent_hash TEXT
);

-- Prevent in-place updates on references.
CREATE OR REPLACE FUNCTION prevent_reference_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'References are immutable; create a new row instead';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS references_update_guard ON references_v1;
CREATE TRIGGER references_update_guard
BEFORE UPDATE ON references_v1
FOR EACH ROW EXECUTE PROCEDURE prevent_reference_update();

CREATE TABLE IF NOT EXISTS protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    registered_on TIMESTAMPTZ NOT NULL,
    locked BOOLEAN NOT NULL DEFAULT FALSE,
    lock_timestamp TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS protocol_amendments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol_id UUID NOT NULL REFERENCES protocols(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    diff JSONB NOT NULL
);

-- Enforce that a locked protocol cannot be edited directly.
CREATE OR REPLACE FUNCTION prevent_locked_protocol_update()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.locked THEN
        RAISE EXCEPTION 'Locked protocol cannot be edited directly; use amendments';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS protocol_lock_guard ON protocols;
CREATE TRIGGER protocol_lock_guard
BEFORE UPDATE ON protocols
FOR EACH ROW EXECUTE PROCEDURE prevent_locked_protocol_update();

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor TEXT NOT NULL CHECK (actor IN ('human', 'agent')),
    user_id UUID,
    action_type TEXT NOT NULL,
    entity TEXT NOT NULL CHECK (entity IN ('Reference', 'Protocol', 'Extraction')),
    entity_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL,
    hash TEXT NOT NULL
);

-- Append-only enforcement: no updates or deletes.
CREATE OR REPLACE FUNCTION prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is append-only';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_update_guard ON audit_logs;
CREATE TRIGGER audit_update_guard
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE PROCEDURE prevent_audit_mutation();

CREATE TABLE IF NOT EXISTS dedup_index (
    digest TEXT PRIMARY KEY,
    reference_id UUID NOT NULL REFERENCES references_v1(id)
);

CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_id UUID NOT NULL REFERENCES references_v1(id),
    user_id UUID NOT NULL,
    location JSONB NOT NULL,
    field TEXT NOT NULL CHECK (field IN ('intervention', 'outcome', 'effect_size')),
    value TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    conflict BOOLEAN DEFAULT FALSE,
    protocol_locked BOOLEAN NOT NULL DEFAULT FALSE,
    pdf_anchor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    extraction_ids UUID[] NOT NULL,
    statement TEXT NOT NULL,
    validated BOOLEAN NOT NULL DEFAULT FALSE,
    invalidated_by JSONB
);

CREATE TABLE IF NOT EXISTS agent_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type TEXT NOT NULL CHECK (type IN ('StatisticalOutput', 'MethodSuggestion', 'HumanInterpretationRequired')),
    generated_by TEXT NOT NULL CHECK (generated_by IN ('rule', 'ai', 'user')),
    source_ids UUID[] NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
