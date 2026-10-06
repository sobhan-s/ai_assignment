-- 01_roles_and_schemas.sql
-- Create a specific read-only role that the AI agent will use for querying
CREATE ROLE sql_agent_ro WITH LOGIN PASSWORD 'agent_secret_ro';

-- Create schemas to separate business data from application logs
CREATE SCHEMA IF NOT EXISTS business;
CREATE SCHEMA IF NOT EXISTS app;

-- Ensure the agent can access the business schema
GRANT USAGE ON SCHEMA business TO sql_agent_ro;
