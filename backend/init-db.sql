-- Chrome Extension History Database Schema
-- This file initializes the database with the complete schema

-- Enable pgvector extension (needed for vector columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- ===========================
-- USERS
-- ===========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    google_user_id TEXT UNIQUE NOT NULL,
    token TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ===========================
-- SESSIONS
-- ===========================
CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_identifier TEXT NOT NULL UNIQUE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_identifier ON sessions(session_identifier);

-- ===========================
-- CLUSTERS
-- ===========================
CREATE TABLE clusters (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,           -- cluster label/theme
    description TEXT,             -- human-readable summary
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_clusters_session_id ON clusters(session_id);
CREATE INDEX idx_clusters_embedding ON clusters USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ===========================
-- HISTORY ITEMS
-- ===========================
CREATE TABLE history_items (
    id SERIAL PRIMARY KEY,
    cluster_id INT NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    domain TEXT,
    visit_time TIMESTAMP NOT NULL,
    raw_semantics JSONB,          -- e.g., extracted keywords, meta info
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_history_items_cluster_id ON history_items(cluster_id);
CREATE INDEX idx_history_items_embedding ON history_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ===========================
-- SAMPLE DATA (for testing)
-- ===========================
INSERT INTO users (google_user_id, token) VALUES ('test_google_id_123', 'test_token_123');

-- ===========================
-- EXAMPLE QUERIES
-- ===========================
-- Get all history items for user_id = 1
-- Optional: filter by session date
-- SELECT hi.*
-- FROM history_items hi
-- JOIN clusters c ON hi.cluster_id = c.id
-- JOIN sessions s ON c.session_id = s.id
-- WHERE s.user_id = 1
--   AND s.start_time >= '2025-10-01'
--   AND s.end_time <= '2025-10-06';
