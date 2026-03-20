-- Enable pgvector extension (we'll use it in Sprint 4)
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── Users ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200),
    email_masked    VARCHAR(200),
    phone_masked    VARCHAR(20),
    tier            VARCHAR(10) DEFAULT 'standard' CHECK (tier IN ('standard','silver','gold','vip')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Seed one test user so Sprint 1 POST /complaint works immediately
INSERT INTO users (user_id, name, email_masked, phone_masked, tier)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Test User',
    'test@example.com',
    '+91-XXXXXXXX10',
    'standard'
) ON CONFLICT DO NOTHING;

-- ─── Complaints ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id          UUID UNIQUE NOT NULL,          -- idempotency key
    user_id             UUID NOT NULL REFERENCES users(user_id),
    channel             VARCHAR(20) NOT NULL CHECK (channel IN ('email','whatsapp','twitter','phone','web','branch','api')),
    message_original    TEXT NOT NULL,
    status              VARCHAR(30) DEFAULT 'received' CHECK (status IN (
                            'received','normalised','ai_processed',
                            'assigned','in_progress','resolved','escalated')),
    schema_version      VARCHAR(10) DEFAULT 'v1.0',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER complaints_updated_at
    BEFORE UPDATE ON complaints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── Audit Log (immutable — no UPDATE/DELETE) ─────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    log_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id    UUID NOT NULL,
    event_type      VARCHAR(50) NOT NULL,   -- received | status_change | escalation
    old_value       JSONB,
    new_value       JSONB,
    actor_type      VARCHAR(10) DEFAULT 'system',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_complaints_user     ON complaints(user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_status   ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_channel  ON complaints(channel);
CREATE INDEX IF NOT EXISTS idx_complaints_created  ON complaints(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_complaint     ON audit_log(complaint_id);
