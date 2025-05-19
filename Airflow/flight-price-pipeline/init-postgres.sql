-- Create databases if they don't exist
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

SELECT 'CREATE DATABASE flight_analytics'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'flight_analytics')\gexec

-- Create roles if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'flight_user') THEN
        CREATE ROLE flight_user WITH LOGIN PASSWORD 'flight_secure_password';
    ELSE
        ALTER ROLE flight_user WITH LOGIN PASSWORD 'flight_secure_password';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analytics_user') THEN
        CREATE ROLE analytics_user WITH LOGIN PASSWORD 'analytics_pass';
    ELSE
        ALTER ROLE analytics_user WITH LOGIN PASSWORD 'analytics_pass';
    END IF;
END $$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE airflow TO flight_user;
GRANT ALL PRIVILEGES ON DATABASE flight_analytics TO analytics_user;

-- Connect to each database to set schema privileges
\c airflow
ALTER SCHEMA public OWNER TO flight_user;
GRANT CREATE, USAGE ON SCHEMA public TO flight_user;

\c flight_analytics
ALTER SCHEMA public OWNER TO analytics_user;
GRANT CREATE, USAGE ON SCHEMA public TO analytics_user;