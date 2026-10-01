#!/bin/sh
set -e

# Wait for PostgreSQL database if DATABASE_URL is configured
if [ -n "$DATABASE_URL" ]; then
    echo "Checking database connectivity..."
    python - <<END
import os, sys, time, urllib.parse
db_url = os.environ.get("DATABASE_URL", "")
if "postgres" in db_url:
    try:
        import psycopg2
        url = urllib.parse.urlparse(db_url)
        for i in range(30):
            try:
                conn = psycopg2.connect(
                    dbname=url.path[1:],
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port or 5432,
                    connect_timeout=2
                )
                conn.close()
                print("PostgreSQL database is ready and accepting connections!")
                sys.exit(0)
            except Exception:
                print(f"Waiting for database at {url.hostname}:{url.port or 5432}... ({i+1}/30)")
                time.sleep(1)
        print("Error: Timed out waiting for database.")
        sys.exit(1)
    except ImportError:
        pass
END
fi

# Run database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static assets
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Execute the main container command
echo "Starting ClinSaarthi AI backend..."
exec "$@"
