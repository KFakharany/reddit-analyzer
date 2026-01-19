-- Reddit Analyzer Database Schema
-- Version: 2.0.0

-- Communities being tracked
CREATE TABLE IF NOT EXISTS communities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    subscribers INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Each data collection run (for time-series tracking)
CREATE TABLE IF NOT EXISTS collection_runs (
    id SERIAL PRIMARY KEY,
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    posts_collected INTEGER DEFAULT 0,
    comments_collected INTEGER DEFAULT 0,
    error_message TEXT
);

-- Posts with versioning
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) NOT NULL,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE CASCADE,
    community_id INTEGER REFERENCES communities(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    selftext TEXT,
    author_name VARCHAR(50),
    score INTEGER,
    upvote_ratio FLOAT,
    num_comments INTEGER,
    flair_text VARCHAR(100),
    is_self BOOLEAN DEFAULT TRUE,
    is_video BOOLEAN DEFAULT FALSE,
    permalink VARCHAR(500),
    created_utc TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(reddit_id, collection_run_id)
);

-- Comments with threading
CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    reddit_id VARCHAR(20) NOT NULL,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE CASCADE,
    parent_reddit_id VARCHAR(20),
    author_name VARCHAR(50),
    body TEXT,
    score INTEGER,
    depth INTEGER DEFAULT 0,
    is_submitter BOOLEAN DEFAULT FALSE,
    created_utc TIMESTAMP,
    collected_at TIMESTAMP DEFAULT NOW()
);

-- Author profiles (fetched separately)
CREATE TABLE IF NOT EXISTS authors (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    link_karma INTEGER,
    comment_karma INTEGER,
    total_karma INTEGER,
    account_created_utc TIMESTAMP,
    is_gold BOOLEAN DEFAULT FALSE,
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Analysis results (one per collection run)
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE CASCADE UNIQUE,
    score_distribution JSONB,
    flair_distribution JSONB,
    timing_patterns JSONB,
    title_analysis JSONB,
    op_engagement_analysis JSONB,
    upvote_ratio_analysis JSONB,
    post_format_analysis JSONB,
    author_success_analysis JSONB,
    sentiment_analysis JSONB,
    pain_point_analysis JSONB,
    tone_analysis JSONB,
    promotion_analysis JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Audience analysis (one per collection run)
CREATE TABLE IF NOT EXISTS audience_analyses (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE CASCADE UNIQUE,
    self_identifications JSONB,
    skill_levels JSONB,
    goals_motivations JSONB,
    pain_points JSONB,
    tools_mentioned JSONB,
    budget_signals JSONB,
    skepticism_level VARCHAR(20),
    personas JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated reports
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    collection_run_id INTEGER REFERENCES collection_runs(id) ON DELETE CASCADE,
    report_type VARCHAR(50),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_posts_community ON posts(community_id);
CREATE INDEX IF NOT EXISTS idx_posts_collection ON posts(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_utc);
CREATE INDEX IF NOT EXISTS idx_posts_score ON posts(score DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_collection ON comments(collection_run_id);
CREATE INDEX IF NOT EXISTS idx_comments_score ON comments(score DESC);
CREATE INDEX IF NOT EXISTS idx_collection_runs_community ON collection_runs(community_id);
CREATE INDEX IF NOT EXISTS idx_collection_runs_status ON collection_runs(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for communities table
DROP TRIGGER IF EXISTS update_communities_updated_at ON communities;
CREATE TRIGGER update_communities_updated_at
    BEFORE UPDATE ON communities
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
