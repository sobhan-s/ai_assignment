-- 03_app_tables.sql
SET search_path TO app;

CREATE TABLE query_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
