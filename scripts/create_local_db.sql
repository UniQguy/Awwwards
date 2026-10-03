-- Electrocart Local Development Database Setup
-- Compatible with PostgreSQL 16, 17, and 18+ on Windows / macOS / Linux.
-- Run as superuser: psql -U postgres -f scripts/create_local_db.sql

-- 1. Create application role if it does not exist, set password, and grant CREATEDB
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'electrocart') THEN
      CREATE ROLE electrocart WITH LOGIN PASSWORD 'electrocart_dev_password';
   ELSE
      ALTER ROLE electrocart WITH LOGIN PASSWORD 'electrocart_dev_password';
   END IF;
END
$do$;

-- CREATEDB is required so Django's test runner can dynamically create and drop test databases (e.g., test_electrocart)
ALTER ROLE electrocart CREATEDB;

-- 2. Create the development database owned by electrocart if it does not exist
SELECT 'CREATE DATABASE electrocart OWNER electrocart ENCODING ''UTF8'' TEMPLATE template1'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'electrocart')\gexec

-- 3. Grant schema permissions (required for PostgreSQL 15+ where public schema permissions were restricted)
\connect electrocart

GRANT ALL PRIVILEGES ON DATABASE electrocart TO electrocart;
GRANT ALL ON SCHEMA public TO electrocart;
ALTER SCHEMA public OWNER TO electrocart;
