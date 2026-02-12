
-- Enable pgvector extension
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
    name TEXT NOT NULL,
    description TEXT,
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
    raw_semantics JSONB,
    embedding VECTOR(768),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_history_items_cluster_id ON history_items(cluster_id);
CREATE INDEX idx_history_items_embedding ON history_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ===========================
-- SAMPLE DATA  (test)
-- ===========================
INSERT INTO users (google_user_id, token) VALUES ('test_google_id_123', 'test_token_123');


