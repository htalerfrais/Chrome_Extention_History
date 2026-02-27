-- DEPRECATED: this bootstrap SQL is intentionally neutralized.
-- Source of truth for schema creation/evolution is now Alembic migrations.
-- Use:
--   alembic upgrade head
--
-- Keeping this file as a no-op avoids drift between static SQL and migrations.
SELECT 'init-db.sql is deprecated; run Alembic migrations (alembic upgrade head).' AS message;
