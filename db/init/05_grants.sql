-- 05_grants.sql
-- Grant SELECT ONLY to the agent role for the business schema
GRANT SELECT ON ALL TABLES IN SCHEMA business TO sql_agent_ro;

-- Ensure future tables also grant SELECT automatically
ALTER DEFAULT PRIVILEGES IN SCHEMA business GRANT SELECT ON TABLES TO sql_agent_ro;

-- The agent role should NOT have access to the app schema (query_log, etc.)
REVOKE ALL ON ALL TABLES IN SCHEMA app FROM sql_agent_ro;
