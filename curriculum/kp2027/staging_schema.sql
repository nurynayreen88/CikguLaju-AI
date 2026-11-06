-- KP2027 isolated staging schema. DO NOT execute against CikguLaju production DB.
-- No default standards or lesson records. No ALTER/DROP of legacy data.
-- Apply ONLY to an explicitly new sidecar file, once original documents are obtained.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS kp2027_source_documents (
    source_id INTEGER PRIMARY KEY,
    level TEXT NOT NULL CHECK (level IN ('Tahun 1', 'Tingkatan 1')),
    subject TEXT NOT NULL,
    title TEXT NOT NULL,
    edition TEXT NOT NULL,
    version_text TEXT NOT NULL,
    source_url TEXT NOT NULL CHECK (source_url LIKE 'https://%'),
    original_pdf_sha256 TEXT NOT NULL CHECK (length(original_pdf_sha256) = 64),
    total_pages INTEGER NOT NULL CHECK (total_pages > 0),
    fetched_utc TEXT NOT NULL,
    verified_by TEXT,
    verified_utc TEXT,
    approval_status TEXT NOT NULL DEFAULT 'DRAF'
       CHECK (approval_status IN ('DRAF','DALAM_SEMAKAN','DILULUSKAN')),
    UNIQUE (level, subject, original_pdf_sha256)
);

CREATE TABLE IF NOT EXISTS kp2027_curriculum_standards (
    standard_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES kp2027_source_documents(source_id),
    standard_kind TEXT NOT NULL,  -- preserve exact source label; never infer from KSSR
    standard_code TEXT,           -- NULL is valid when DK has no numeric code
    standard_text TEXT NOT NULL,
    source_page INTEGER NOT NULL CHECK (source_page > 0),
    source_section TEXT NOT NULL,
    reviewer TEXT,
    reviewed_utc TEXT,
    audit_status TEXT NOT NULL DEFAULT 'DRAF'
       CHECK (audit_status IN ('DRAF','SEMAK','LULUS')),
    UNIQUE (source_id, standard_kind, standard_code, source_page)
);

CREATE TABLE IF NOT EXISTS kp2027_learning_sequences (
    sequence_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES kp2027_source_documents(source_id),
    pdp_no INTEGER NOT NULL CHECK (pdp_no >= 1),
    theme TEXT,
    unit_title TEXT,
    topic TEXT NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes BETWEEN 20 AND 180),
    status TEXT NOT NULL DEFAULT 'DRAF'
       CHECK (status IN ('DRAF','SEMAK','READY')),
    UNIQUE (source_id, pdp_no)
);

CREATE TABLE IF NOT EXISTS kp2027_sequence_standards (
    sequence_id INTEGER NOT NULL REFERENCES kp2027_learning_sequences(sequence_id),
    standard_id INTEGER NOT NULL REFERENCES kp2027_curriculum_standards(standard_id),
    PRIMARY KEY (sequence_id, standard_id)
);

CREATE INDEX IF NOT EXISTS kp2027_idx_source_level
    ON kp2027_source_documents(level, subject, approval_status);

CREATE INDEX IF NOT EXISTS kp2027_idx_sequence_source
    ON kp2027_learning_sequences(source_id, pdp_no);

-- Activation gate is implemented in app logic, NOT implied by writing to staging.
-- Every READY sequence must have audited standards, same source and approved DK.
-- Never silently substitute a legacy KSSR/KSSM file or lesson record.
