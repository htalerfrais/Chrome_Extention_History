# Database migrations policy

Alembic is the single source of truth for schema lifecycle in this project.

## Mandatory rule

- Do **not** use `init-db.sql` to create/upgrade schema.
- Always use Alembic:
  - `alembic upgrade head` to apply latest schema
  - `alembic downgrade -1` to rollback one migration

## Why

- Prevent schema drift between environments.
- Keep schema history versioned and auditable.
- Ensure reproducible deploys and safe rollbacks.

## Current baseline

- Baseline migration: `alembic/versions/0001_modular_convergence.py`
- This migration creates the full current schema (users, sessions, clusters, history, topics, recall, quiz, outbox).
