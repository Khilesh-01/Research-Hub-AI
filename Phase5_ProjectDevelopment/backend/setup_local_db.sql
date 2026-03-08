-- Create user and database in the local Windows PostgreSQL
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'Smartbridge') THEN
        CREATE USER "Smartbridge" WITH PASSWORD 'Smartbridge123';
    ELSE
        ALTER USER "Smartbridge" WITH PASSWORD 'Smartbridge123';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ResearchHub') THEN
        CREATE DATABASE "ResearchHub" OWNER "Smartbridge";
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE "ResearchHub" TO "Smartbridge";
