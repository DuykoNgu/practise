-- Change-Incident Correlation (CIC) — PostgreSQL schema
-- Design status: TARGET V1. Target: PostgreSQL 15+ (uses NULLS NOT DISTINCT).
-- Source of truth for docs/06-data-model.md and docs/DATABASE.md.

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;    -- case-insensitive e-mail

CREATE SCHEMA IF NOT EXISTS cic;
SET search_path TO cic, public;

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------
CREATE TYPE user_role        AS ENUM ('ADMIN', 'IT_MANAGER', 'CHANGE_ENGINEER', 'AGENT');
CREATE TYPE api_client_kind  AS ENUM ('ITSM', 'LOG_SOURCE');
CREATE TYPE record_source    AS ENUM ('MANUAL', 'IMPORT', 'API');
CREATE TYPE change_type      AS ENUM ('PATCH', 'CONFIG_CHANGE', 'SOFTWARE_UPGRADE');
CREATE TYPE change_status    AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'ROLLED_BACK', 'FAILED');
CREATE TYPE ticket_status    AS ENUM ('NEW', 'IN_PROGRESS', 'RESOLVED', 'CLOSED');
CREATE TYPE import_status    AS ENUM ('SUCCEEDED', 'FAILED');
CREATE TYPE log_level        AS ENUM ('WARNING', 'ERROR', 'CRITICAL');
CREATE TYPE severity         AS ENUM ('HIGH', 'MEDIUM', 'LOW');
CREATE TYPE anomaly_status   AS ENUM ('OPEN', 'ACKNOWLEDGED', 'RESOLVED');
CREATE TYPE run_status       AS ENUM ('RUNNING', 'SUCCEEDED', 'FAILED');
CREATE TYPE score_factor     AS ENUM ('TIME_PROXIMITY', 'SCOPE_MATCH', 'CATEGORY_KEYWORD_MATCH', 'ANOMALY_MAGNITUDE', 'CHANGE_RISK');
CREATE TYPE feedback_verdict AS ENUM ('CORRECT_CAUSE', 'UNRELATED');
CREATE TYPE suggestion_status AS ENUM ('PENDING', 'READY', 'NO_SUPPORT', 'FAILED');
CREATE TYPE suggestion_label AS ENUM ('CONFIRMED', 'HYPOTHESIS');
CREATE TYPE suggestion_decision AS ENUM ('CONFIRMED', 'REJECTED');
CREATE TYPE statement_kind   AS ENUM ('CAUSE', 'STEP');
CREATE TYPE statement_basis  AS ENUM ('STANDARD', 'LLM_KNOWLEDGE');
CREATE TYPE evidence_type    AS ENUM ('LOG', 'TICKET', 'CHANGE', 'ROLLBACK_PLAN', 'PAST_INCIDENT', 'GUIDELINE');
CREATE TYPE job_type         AS ENUM ('BASELINE_RECOMPUTE', 'ANOMALY_DETECTION', 'LOG_CLASSIFICATION', 'SUGGESTION_GENERATION');
CREATE TYPE job_status       AS ENUM ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED');
CREATE TYPE audit_action     AS ENUM ('LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'STATUS_CHANGE', 'IMPORT',
                                      'CONFIG_CHANGE', 'FEEDBACK', 'SUGGESTION_DECISION', 'BASELINE_RECOMPUTE');

-- ---------------------------------------------------------------------------
-- Shared helper: keep updated_at current
-- ---------------------------------------------------------------------------
CREATE FUNCTION set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;

-- ---------------------------------------------------------------------------
-- Identity and integration clients
-- ---------------------------------------------------------------------------
CREATE TABLE app_users (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name      varchar(120) NOT NULL,
  email          citext       NOT NULL UNIQUE,
  phone          varchar(30),
  avatar_url     text,
  password_hash  text         NOT NULL,
  role           user_role    NOT NULL,
  is_active      boolean      NOT NULL DEFAULT true,
  last_login_at  timestamptz,
  created_at     timestamptz  NOT NULL DEFAULT now(),
  updated_at     timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE api_clients (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          varchar(120)    NOT NULL UNIQUE,
  kind          api_client_kind NOT NULL,
  key_hash      text            NOT NULL UNIQUE,   -- only the hash of X-API-Key is stored
  is_active     boolean         NOT NULL DEFAULT true,
  last_used_at  timestamptz,
  created_at    timestamptz     NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Scope dimensions (lookups). Shared by changes, tickets, logs, anomalies so
-- that scope matching compares ids, not free text.
-- ---------------------------------------------------------------------------
CREATE TABLE departments (
  id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code  varchar(30)  NOT NULL UNIQUE,
  name  varchar(120) NOT NULL
);

CREATE TABLE branches (
  id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code  varchar(30)  NOT NULL UNIQUE,
  name  varchar(120) NOT NULL
);

CREATE TABLE software (
  id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name  varchar(120) NOT NULL UNIQUE
);

CREATE TABLE device_groups (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name           varchar(120) NOT NULL UNIQUE,
  department_id  uuid REFERENCES departments(id),  -- used to map a log's device to a department
  branch_id      uuid REFERENCES branches(id)
);
CREATE INDEX ON device_groups (department_id);
CREATE INDEX ON device_groups (branch_id);

CREATE TABLE categories (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name      varchar(120) NOT NULL UNIQUE,
  keywords  text[]       NOT NULL DEFAULT '{}'  -- used by the category/keyword match factor
);

-- ---------------------------------------------------------------------------
-- Changes and their scope (rollback plan is 1:1, stored inline)
-- ---------------------------------------------------------------------------
CREATE TABLE changes (
  id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source                      record_source NOT NULL,
  source_client_id            uuid REFERENCES api_clients(id),
  external_id                 varchar(120),
  type                        change_type   NOT NULL,
  title                       varchar(200)  NOT NULL,
  description                 text,
  start_at                    timestamptz   NOT NULL,
  end_at                      timestamptz,
  status                      change_status NOT NULL,
  implementer_id              uuid          NOT NULL REFERENCES app_users(id),
  approver_id                 uuid          REFERENCES app_users(id),
  rollback_available          boolean       NOT NULL,
  rollback_steps              text,
  rollback_estimated_minutes  integer       CHECK (rollback_estimated_minutes >= 0),
  rollback_risk               severity,
  created_by                  uuid          REFERENCES app_users(id),  -- NULL when pushed through the API
  created_at                  timestamptz   NOT NULL DEFAULT now(),
  updated_at                  timestamptz   NOT NULL DEFAULT now(),
  CHECK (end_at IS NULL OR end_at >= start_at),
  CHECK (NOT rollback_available OR rollback_steps IS NOT NULL),
  CHECK ((source = 'API') = (source_client_id IS NOT NULL)),
  CHECK (source <> 'API' OR external_id IS NOT NULL),
  UNIQUE (source_client_id, external_id)
);
CREATE INDEX ON changes (start_at);
CREATE INDEX ON changes (implementer_id);
CREATE INDEX ON changes (approver_id);
CREATE INDEX ON changes (created_by);
CREATE INDEX ON changes (status);

CREATE TABLE change_departments (
  change_id      uuid NOT NULL REFERENCES changes(id) ON DELETE CASCADE,
  department_id  uuid NOT NULL REFERENCES departments(id),
  PRIMARY KEY (change_id, department_id)
);
CREATE INDEX ON change_departments (department_id);

CREATE TABLE change_branches (
  change_id  uuid NOT NULL REFERENCES changes(id) ON DELETE CASCADE,
  branch_id  uuid NOT NULL REFERENCES branches(id),
  PRIMARY KEY (change_id, branch_id)
);
CREATE INDEX ON change_branches (branch_id);

CREATE TABLE change_software (
  change_id    uuid NOT NULL REFERENCES changes(id) ON DELETE CASCADE,
  software_id  uuid NOT NULL REFERENCES software(id),
  PRIMARY KEY (change_id, software_id)
);
CREATE INDEX ON change_software (software_id);

CREATE TABLE change_device_groups (
  change_id        uuid NOT NULL REFERENCES changes(id) ON DELETE CASCADE,
  device_group_id  uuid NOT NULL REFERENCES device_groups(id),
  PRIMARY KEY (change_id, device_group_id)
);
CREATE INDEX ON change_device_groups (device_group_id);

-- ---------------------------------------------------------------------------
-- Tickets and import batches
-- ---------------------------------------------------------------------------
CREATE TABLE import_batches (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name      varchar(255)  NOT NULL,
  storage_key    text          NOT NULL,
  status         import_status NOT NULL,
  total_rows     integer       NOT NULL CHECK (total_rows >= 0),
  imported_rows  integer       NOT NULL CHECK (imported_rows >= 0),
  errors         jsonb         NOT NULL DEFAULT '[]',  -- row-level validation errors
  created_by     uuid          NOT NULL REFERENCES app_users(id),
  created_at     timestamptz   NOT NULL DEFAULT now(),
  CHECK (imported_rows <= total_rows),
  CHECK (status = 'SUCCEEDED' OR imported_rows = 0)  -- import is atomic
);
CREATE INDEX ON import_batches (created_by);
CREATE INDEX ON import_batches (created_at);

CREATE TABLE tickets (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source            record_source NOT NULL,
  source_client_id  uuid REFERENCES api_clients(id),
  external_id       varchar(120),
  import_batch_id   uuid REFERENCES import_batches(id),
  reported_at       timestamptz   NOT NULL,
  category_id       uuid          NOT NULL REFERENCES categories(id),
  department_id     uuid          NOT NULL REFERENCES departments(id),
  branch_id         uuid          NOT NULL REFERENCES branches(id),
  device_group_id   uuid          REFERENCES device_groups(id),
  software_id       uuid          REFERENCES software(id),
  software_version  varchar(60),
  description       text          NOT NULL,
  status            ticket_status NOT NULL DEFAULT 'NEW',
  created_by        uuid          REFERENCES app_users(id),  -- NULL when pushed through the API
  created_at        timestamptz   NOT NULL DEFAULT now(),
  updated_at        timestamptz   NOT NULL DEFAULT now(),
  CHECK ((source = 'API') = (source_client_id IS NOT NULL)),
  CHECK ((source = 'IMPORT') = (import_batch_id IS NOT NULL)),
  CHECK (source <> 'API' OR external_id IS NOT NULL),
  UNIQUE (source_client_id, external_id)
);
-- Anomaly detection counts tickets per time bucket and group.
CREATE INDEX ON tickets (reported_at);
CREATE INDEX ON tickets (category_id, reported_at);
CREATE INDEX ON tickets (department_id, reported_at);
CREATE INDEX ON tickets (branch_id, reported_at);
CREATE INDEX ON tickets (software_id);
CREATE INDEX ON tickets (device_group_id);
CREATE INDEX ON tickets (import_batch_id);
CREATE INDEX ON tickets (created_by);

-- ---------------------------------------------------------------------------
-- Error logs (message is masked before insert; raw message is never stored)
-- ---------------------------------------------------------------------------
CREATE TABLE error_logs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_client_id  uuid         NOT NULL REFERENCES api_clients(id),
  external_id       varchar(120) NOT NULL,
  occurred_at       timestamptz  NOT NULL,
  level             log_level    NOT NULL,
  software_id       uuid REFERENCES software(id),
  device_group_id   uuid REFERENCES device_groups(id),
  department_id     uuid REFERENCES departments(id),   -- from payload, or mapped from device_groups
  branch_id         uuid REFERENCES branches(id),
  code              varchar(120),
  message_masked    text         NOT NULL,
  signature         char(64),                         -- SHA-256 of the normalized message; set by the worker
  category_id       uuid REFERENCES categories(id),   -- set by the worker
  received_at       timestamptz  NOT NULL DEFAULT now(),
  UNIQUE (source_client_id, external_id)
);
CREATE INDEX ON error_logs (occurred_at);
CREATE INDEX ON error_logs (signature);
CREATE INDEX ON error_logs (received_at);            -- retention cleanup
CREATE INDEX ON error_logs (software_id);
CREATE INDEX ON error_logs (device_group_id);
CREATE INDEX ON error_logs (department_id);
CREATE INDEX ON error_logs (branch_id);
CREATE INDEX ON error_logs (category_id);
CREATE INDEX error_logs_unclassified ON error_logs (received_at) WHERE signature IS NULL;

-- ---------------------------------------------------------------------------
-- Baseline (one run = one recompute; the latest SUCCEEDED run is active)
-- ---------------------------------------------------------------------------
CREATE TABLE baseline_runs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  status        run_status  NOT NULL DEFAULT 'RUNNING',
  window_weeks  integer     NOT NULL CHECK (window_weeks > 0),
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz
);
CREATE INDEX ON baseline_runs (status, finished_at);

-- department_id / branch_id NULL means "all departments" / "all branches".
CREATE TABLE baseline_cells (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  baseline_run_id  uuid     NOT NULL REFERENCES baseline_runs(id) ON DELETE CASCADE,
  category_id      uuid     NOT NULL REFERENCES categories(id),
  department_id    uuid     REFERENCES departments(id),
  branch_id        uuid     REFERENCES branches(id),
  weekday          smallint NOT NULL CHECK (weekday BETWEEN 1 AND 7),  -- ISO: 1 = Monday
  hour             smallint NOT NULL CHECK (hour BETWEEN 0 AND 23),
  mean             numeric(10,3) NOT NULL CHECK (mean >= 0),
  std_dev          numeric(10,3) NOT NULL CHECK (std_dev >= 0),
  sample_weeks     smallint NOT NULL CHECK (sample_weeks > 0),
  UNIQUE NULLS NOT DISTINCT (baseline_run_id, category_id, department_id, branch_id, weekday, hour)
);
CREATE INDEX ON baseline_cells (category_id);
CREATE INDEX ON baseline_cells (department_id);
CREATE INDEX ON baseline_cells (branch_id);

-- ---------------------------------------------------------------------------
-- Anomalies and what they contain
-- ---------------------------------------------------------------------------
CREATE TABLE anomalies (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  baseline_run_id  uuid           NOT NULL REFERENCES baseline_runs(id),
  category_id      uuid REFERENCES categories(id),
  department_id    uuid REFERENCES departments(id),
  branch_id        uuid REFERENCES branches(id),
  software_id      uuid REFERENCES software(id),
  start_at         timestamptz    NOT NULL,
  end_at           timestamptz,
  actual_count     integer        NOT NULL CHECK (actual_count >= 0),
  expected_count   numeric(10,3)  NOT NULL CHECK (expected_count >= 0),
  severity         severity       NOT NULL,
  status           anomaly_status NOT NULL DEFAULT 'OPEN',
  detected_at      timestamptz    NOT NULL DEFAULT now(),
  updated_at       timestamptz    NOT NULL DEFAULT now(),
  CHECK (num_nonnulls(category_id, department_id, branch_id, software_id) >= 1),
  CHECK (end_at IS NULL OR end_at >= start_at)
);
CREATE INDEX ON anomalies (status, start_at);
CREATE INDEX ON anomalies (baseline_run_id);
CREATE INDEX ON anomalies (category_id);
CREATE INDEX ON anomalies (department_id);
CREATE INDEX ON anomalies (branch_id);
CREATE INDEX ON anomalies (software_id);

CREATE TABLE anomaly_tickets (
  anomaly_id  uuid NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
  ticket_id   uuid NOT NULL REFERENCES tickets(id),
  PRIMARY KEY (anomaly_id, ticket_id)
);
CREATE INDEX ON anomaly_tickets (ticket_id);

-- Log links disappear with the log when retention deletes it.
CREATE TABLE anomaly_logs (
  anomaly_id    uuid NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
  error_log_id  uuid NOT NULL REFERENCES error_logs(id) ON DELETE CASCADE,
  PRIMARY KEY (anomaly_id, error_log_id)
);
CREATE INDEX ON anomaly_logs (error_log_id);

-- ---------------------------------------------------------------------------
-- Suspects, score factors, feedback
-- ---------------------------------------------------------------------------
CREATE TABLE suspects (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  anomaly_id  uuid     NOT NULL REFERENCES anomalies(id) ON DELETE CASCADE,
  change_id   uuid     NOT NULL REFERENCES changes(id),
  rank        smallint NOT NULL CHECK (rank >= 1),
  score       smallint NOT NULL CHECK (score BETWEEN 0 AND 100),
  level       severity NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (anomaly_id, change_id),
  UNIQUE (anomaly_id, rank)
);
CREATE INDEX ON suspects (change_id);

CREATE TABLE suspect_factors (
  suspect_id    uuid         NOT NULL REFERENCES suspects(id) ON DELETE CASCADE,
  factor        score_factor NOT NULL,
  contribution  numeric(6,2) NOT NULL,
  explanation   text         NOT NULL,
  PRIMARY KEY (suspect_id, factor)
);

-- One verdict per user per suspect; a new verdict replaces the old one.
CREATE TABLE suspect_feedback (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  suspect_id  uuid             NOT NULL REFERENCES suspects(id) ON DELETE CASCADE,
  user_id     uuid             NOT NULL REFERENCES app_users(id),
  verdict     feedback_verdict NOT NULL,
  note        varchar(1000),
  created_at  timestamptz      NOT NULL DEFAULT now(),
  updated_at  timestamptz      NOT NULL DEFAULT now(),
  UNIQUE (suspect_id, user_id)
);
CREATE INDEX ON suspect_feedback (user_id);

-- ---------------------------------------------------------------------------
-- Internal guidance ("standard" resolutions that are not a rollback plan or a
-- past incident)
-- ---------------------------------------------------------------------------
CREATE TABLE guidelines (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title        varchar(200) NOT NULL,
  body         text         NOT NULL,
  category_id  uuid REFERENCES categories(id),
  software_id  uuid REFERENCES software(id),
  created_by   uuid NOT NULL REFERENCES app_users(id),
  created_at   timestamptz  NOT NULL DEFAULT now(),
  updated_at   timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ON guidelines (category_id);
CREATE INDEX ON guidelines (software_id);
CREATE INDEX ON guidelines (created_by);

-- ---------------------------------------------------------------------------
-- Suggested resolutions (versioned; the highest version is current)
-- ---------------------------------------------------------------------------
CREATE TABLE suggestions (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  suspect_id     uuid              NOT NULL REFERENCES suspects(id) ON DELETE CASCADE,
  version        smallint          NOT NULL CHECK (version >= 1),
  status         suggestion_status NOT NULL DEFAULT 'PENDING',
  label          suggestion_label  NOT NULL DEFAULT 'HYPOTHESIS',
  model_name     varchar(120),
  generated_at   timestamptz,
  decision       suggestion_decision,
  decided_by     uuid REFERENCES app_users(id),
  decided_at     timestamptz,
  decision_note  varchar(1000),
  created_at     timestamptz       NOT NULL DEFAULT now(),
  UNIQUE (suspect_id, version),
  CHECK ((decision IS NULL) = (decided_by IS NULL) AND (decision IS NULL) = (decided_at IS NULL)),
  CHECK (label <> 'CONFIRMED' OR decision IS NOT DISTINCT FROM 'CONFIRMED'),
  CHECK (decision IS NULL OR status = 'READY')
);
CREATE INDEX ON suggestions (decided_by);

CREATE TABLE suggestion_statements (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  suggestion_id  uuid            NOT NULL REFERENCES suggestions(id) ON DELETE CASCADE,
  kind           statement_kind  NOT NULL,
  position       smallint        NOT NULL CHECK (position >= 1),
  text           text            NOT NULL,
  basis          statement_basis NOT NULL,
  UNIQUE (suggestion_id, kind, position),
  CHECK (kind <> 'CAUSE' OR basis = 'STANDARD')  -- a cause is always evidence-based
);

-- Exactly one typed reference per evidence row.
CREATE TABLE statement_evidence (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  statement_id        uuid          NOT NULL REFERENCES suggestion_statements(id) ON DELETE CASCADE,
  type                evidence_type NOT NULL,
  error_log_id        uuid REFERENCES error_logs(id) ON DELETE SET NULL,
  ticket_id           uuid REFERENCES tickets(id),
  change_id           uuid REFERENCES changes(id),
  past_suggestion_id  uuid REFERENCES suggestions(id),
  guideline_id        uuid REFERENCES guidelines(id) ON DELETE SET NULL,
  log_snapshot        text,  -- masked excerpt kept so evidence survives log retention
  note                text,
  CHECK (
    (type = 'LOG'           AND ticket_id IS NULL AND change_id IS NULL AND past_suggestion_id IS NULL AND guideline_id IS NULL AND (error_log_id IS NOT NULL OR log_snapshot IS NOT NULL)) OR
    (type = 'TICKET'        AND num_nonnulls(ticket_id) = 1 AND num_nonnulls(error_log_id, change_id, past_suggestion_id, guideline_id) = 0) OR
    (type IN ('CHANGE', 'ROLLBACK_PLAN') AND num_nonnulls(change_id) = 1 AND num_nonnulls(error_log_id, ticket_id, past_suggestion_id, guideline_id) = 0) OR
    (type = 'PAST_INCIDENT' AND num_nonnulls(past_suggestion_id) = 1 AND num_nonnulls(error_log_id, ticket_id, change_id, guideline_id) = 0) OR
    (type = 'GUIDELINE'     AND num_nonnulls(error_log_id, ticket_id, change_id, past_suggestion_id) = 0 AND (guideline_id IS NOT NULL OR note IS NOT NULL))
  )
);
CREATE INDEX ON statement_evidence (statement_id);
CREATE INDEX ON statement_evidence (error_log_id);
CREATE INDEX ON statement_evidence (ticket_id);
CREATE INDEX ON statement_evidence (change_id);
CREATE INDEX ON statement_evidence (past_suggestion_id);
CREATE INDEX ON statement_evidence (guideline_id);

-- ---------------------------------------------------------------------------
-- Job table shared by the Backend API (producer) and the Analysis Worker
-- (consumer: SELECT ... FOR UPDATE SKIP LOCKED)
-- ---------------------------------------------------------------------------
CREATE TABLE jobs (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type         job_type    NOT NULL,
  status       job_status  NOT NULL DEFAULT 'QUEUED',
  payload      jsonb       NOT NULL DEFAULT '{}',
  attempts     smallint    NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  max_attempts smallint    NOT NULL DEFAULT 3 CHECK (max_attempts >= 1),
  run_after    timestamptz NOT NULL DEFAULT now(),
  locked_at    timestamptz,
  locked_by    varchar(120),
  last_error   text,
  created_by   uuid REFERENCES app_users(id),  -- NULL for scheduled jobs
  created_at   timestamptz NOT NULL DEFAULT now(),
  finished_at  timestamptz
);
CREATE INDEX jobs_ready ON jobs (run_after) WHERE status = 'QUEUED';
CREATE INDEX ON jobs (created_by);

-- ---------------------------------------------------------------------------
-- Settings (exactly one row)
-- ---------------------------------------------------------------------------
CREATE TABLE settings (
  id                          smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  anomaly_threshold           numeric(5,2) NOT NULL DEFAULT 3.00 CHECK (anomaly_threshold > 0),  -- std deviations
  tracing_window_hours        integer      NOT NULL DEFAULT 48 CHECK (tracing_window_hours BETWEEN 1 AND 720),
  baseline_window_weeks       integer      NOT NULL DEFAULT 8  CHECK (baseline_window_weeks BETWEEN 1 AND 52),
  detection_interval_minutes  integer      NOT NULL DEFAULT 15 CHECK (detection_interval_minutes BETWEEN 1 AND 1440),
  log_retention_days          integer      NOT NULL DEFAULT 30 CHECK (log_retention_days BETWEEN 1 AND 365),
  weight_time_proximity       numeric(4,2) NOT NULL DEFAULT 1 CHECK (weight_time_proximity >= 0),
  weight_scope_match          numeric(4,2) NOT NULL DEFAULT 1 CHECK (weight_scope_match >= 0),
  weight_category_keyword     numeric(4,2) NOT NULL DEFAULT 1 CHECK (weight_category_keyword >= 0),
  weight_anomaly_magnitude    numeric(4,2) NOT NULL DEFAULT 1 CHECK (weight_anomaly_magnitude >= 0),
  weight_change_risk          numeric(4,2) NOT NULL DEFAULT 1 CHECK (weight_change_risk >= 0),
  updated_by                  uuid REFERENCES app_users(id),
  updated_at                  timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ON settings (updated_by);
INSERT INTO settings (id) VALUES (1);

-- ---------------------------------------------------------------------------
-- Audit log (append-only). Never store passwords, hashes, tokens, or API keys
-- in details.
-- ---------------------------------------------------------------------------
CREATE TABLE audit_logs (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_user_id  uuid REFERENCES app_users(id),
  actor_client_id uuid REFERENCES api_clients(id),
  action         audit_action NOT NULL,
  object_type    varchar(60)  NOT NULL,
  object_id      varchar(120),
  details        jsonb        NOT NULL DEFAULT '{}',
  created_at     timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX ON audit_logs (created_at);
CREATE INDEX ON audit_logs (actor_user_id, created_at);
CREATE INDEX ON audit_logs (actor_client_id);

-- ---------------------------------------------------------------------------
-- updated_at triggers
-- ---------------------------------------------------------------------------
CREATE TRIGGER app_users_updated_at        BEFORE UPDATE ON app_users        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER changes_updated_at          BEFORE UPDATE ON changes          FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER tickets_updated_at          BEFORE UPDATE ON tickets          FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER anomalies_updated_at        BEFORE UPDATE ON anomalies        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER suspect_feedback_updated_at BEFORE UPDATE ON suspect_feedback FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER guidelines_updated_at       BEFORE UPDATE ON guidelines       FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER settings_updated_at         BEFORE UPDATE ON settings         FOR EACH ROW EXECUTE FUNCTION set_updated_at();
