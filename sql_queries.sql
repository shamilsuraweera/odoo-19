-- ==============================================================================
--                       ODOO 19 POSTGRESQL QUERIES CHEAT SHEET
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. USER & ROLE MANAGEMENT
-- ------------------------------------------------------------------------------

-- Create 'odoo' user with password
CREATE USER odoo WITH PASSWORD 'odoo';

-- Grant permission to create databases
ALTER USER odoo WITH CREATEDB;

-- (Optional) Grant superuser privileges for development ease
-- ALTER USER odoo WITH SUPERUSER;

-- Change user password
-- ALTER USER odoo WITH PASSWORD 'new_password';

-- List all PostgreSQL users and their attributes
SELECT usename, usecreatedb, usesuper FROM pg_user;

-- Drop user (Make sure no database is owned by this user first)
-- DROP USER IF EXISTS odoo;


-- ------------------------------------------------------------------------------
-- 2. DATABASE CREATION, CONNECTION TERMINATION & DROPPING
-- ------------------------------------------------------------------------------

-- Create a new blank database owned by 'odoo'
CREATE DATABASE "odoo-19" OWNER odoo;

-- List all databases
SELECT datname, pg_size_pretty(pg_database_size(datname)) AS db_size 
FROM pg_database 
WHERE datistemplate = false;

-- Terminate all active connections to the database (Crucial before dropping or restoring)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'odoo-19' AND pid <> pg_backend_pid();

-- Drop database safely
DROP DATABASE IF EXISTS "odoo-19";


-- ------------------------------------------------------------------------------
-- 3. MODULE STATUS INSPECTION & RECOVERY
-- (Run these inside the specific Odoo database)
-- ------------------------------------------------------------------------------

-- Check state of all installed or updating modules
SELECT name, state, latest_version
FROM ir_module_module
WHERE state IN ('installed', 'to upgrade', 'to install', 'to remove')
ORDER BY name ASC;

-- Fix stuck module state (e.g. when an upgrade crashes mid-way)
UPDATE ir_module_module 
SET state = 'installed' 
WHERE state = 'to upgrade';

UPDATE ir_module_module 
SET state = 'uninstalled' 
WHERE state = 'to install';


-- ------------------------------------------------------------------------------
-- 4. USER ADMINISTRATION & PASSWORD RESET
-- ------------------------------------------------------------------------------

-- List all system users and login details
SELECT id, login, name, active 
FROM res_users 
ORDER BY id ASC;

-- Reset administrator password to 'admin' (Odoo re-hashes plain text on next login)
UPDATE res_users 
SET password = 'admin' 
WHERE login = 'admin';

-- Unlock a blocked/deactivated admin user
UPDATE res_users 
SET active = True 
WHERE login = 'admin';


-- ------------------------------------------------------------------------------
-- 5. SYSTEM PARAMETERS (BASE URL & CONFIG)
-- ------------------------------------------------------------------------------

-- View current base URL configuration
SELECT key, value 
FROM ir_config_parameter 
WHERE key LIKE 'web.base.url%';

-- Set correct local web base URL
UPDATE ir_config_parameter
SET value = 'http://localhost:8069'
WHERE key = 'web.base.url';

-- Freeze web.base.url so Odoo does not automatically rewrite it based on incoming requests
INSERT INTO ir_config_parameter (key, value)
VALUES ('web.base.url.freeze', 'True')
ON CONFLICT (key) DO UPDATE SET value = 'True';


-- ------------------------------------------------------------------------------
-- 6. SCHEDULED ACTIONS / CRONS (DEBUGGING)
-- ------------------------------------------------------------------------------

-- List active scheduled actions
SELECT id, name, model_id, state, active, nextcall, interval_number, interval_type
FROM ir_cron
WHERE active = True
ORDER BY nextcall ASC;

-- Disable all cron jobs (useful during local debugging to avoid background noise)
-- UPDATE ir_cron SET active = False;

-- Re-enable all cron jobs
-- UPDATE ir_cron SET active = True;


-- ------------------------------------------------------------------------------
-- 7. STORAGE & DATABASE DIAGNOSTICS
-- ------------------------------------------------------------------------------

-- Get exact size of the current database
SELECT pg_size_pretty(pg_database_size(current_database())) AS database_size;

-- Summary of binary attachments stored in database/filestore
SELECT count(*) AS total_attachments, pg_size_pretty(sum(file_size)::bigint) AS total_file_size
FROM ir_attachment 
WHERE type = 'binary';