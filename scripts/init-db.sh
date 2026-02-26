#!/bin/bash
# Database initialization script
# This script runs automatically when the PostgreSQL container starts

set -e

echo "Initializing Navi database..."

# The database is already created by POSTGRES_DB environment variable
# This script can be used for additional initialization if needed

# Create extensions if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Enable pgcrypto for additional encryption functions
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL

echo "Database initialization complete!"
