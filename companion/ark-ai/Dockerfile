FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt requirements-postgres.txt ./
# psycopg2-binary is only needed when DATABASE_URL is set to PostgreSQL, but
# it's small and installing it unconditionally keeps the image usable either
# way without rebuilding.
RUN pip install --no-cache-dir -r requirements-postgres.txt

COPY app.py auth.py db.py migrations.py relay.png ./
COPY templates ./templates

ENV ARK_AI_PORT=5000
ENV ARK_AI_HOST=0.0.0.0
ENV ARK_AI_DB_PATH=/data/ark_ai.db
VOLUME ["/data"]
EXPOSE 5000
# ARK_AI_TOKEN must be set to a secret value, and ARK_AI_SECRET_KEY to a
# stable random value, for remote (non-loopback) access to be
# permitted/persistent. (The old RELAY_TOKEN/RELAY_SECRET_KEY/RELAY_* names
# still work as fallbacks.) Set DATABASE_URL to a postgres:// URL to use
# PostgreSQL instead of the SQLite file in /data; schema migrations run
# automatically on startup either way.

CMD ["python", "app.py"]
