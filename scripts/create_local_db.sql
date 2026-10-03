-- Electrocart Local Development Database Setup
-- Run via: psql -U postgres -v app_password='your_password' -f scripts/create_local_db.sql

-- 1. Create or update application role with dynamic password interpolation
SELECT format('CREATE ROLE electrocart WITH LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'electrocart')\gexec

SELECT format('ALTER ROLE electrocart WITH LOGIN PASSWORD %L', :'app_password')
WHERE EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'electrocart')\gexec

-- 2. Grant CREATEDB for Django test runner execution
ALTER ROLE electrocart CREATEDB;

-- 3. Create development database owned by electrocart if it does not exist
SELECT 'CREATE DATABASE electrocart OWNER electrocart ENCODING ''UTF8'' TEMPLATE template1'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'electrocart')\gexec
