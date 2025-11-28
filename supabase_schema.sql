-- Wordle Stats Database Schema for Supabase
-- Execute this in Supabase SQL Editor to create the tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- CORE TABLES
-- ==========================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index on email for fast lookups
CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);

-- Wordle words table (puzzle information)
CREATE TABLE IF NOT EXISTS wordle_words (
    id SERIAL PRIMARY KEY,
    game_date DATE UNIQUE NOT NULL,
    wordle_number INTEGER UNIQUE NOT NULL,
    word VARCHAR(5) NOT NULL
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS wordle_words_date_idx ON wordle_words(game_date);
CREATE INDEX IF NOT EXISTS wordle_words_num_idx ON wordle_words(wordle_number);

-- Scores table (individual game results)
CREATE TABLE IF NOT EXISTS scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wordle_word_id INTEGER NOT NULL REFERENCES wordle_words(id) ON DELETE CASCADE,
    guesses INTEGER NOT NULL CHECK (guesses >= 1 AND guesses <= 7),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_puzzle UNIQUE(user_id, wordle_word_id)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS scores_user_idx ON scores(user_id);
CREATE INDEX IF NOT EXISTS scores_puzzle_idx ON scores(wordle_word_id);
CREATE INDEX IF NOT EXISTS scores_guesses_idx ON scores(guesses);

-- ==========================================
-- OPTIONAL PERFORMANCE OPTIMIZATION TABLE
-- Add this later when dashboard becomes slow
-- ==========================================

-- User statistics cache table
CREATE TABLE IF NOT EXISTS user_stats_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type TEXT NOT NULL CHECK (period_type IN ('week', 'month', 'year', 'all_time')),
    period_year INTEGER,
    period_value INTEGER,

    -- Core statistics
    games_played INTEGER DEFAULT 0,
    games_solved INTEGER DEFAULT 0,
    games_failed INTEGER DEFAULT 0,
    total_guesses INTEGER DEFAULT 0,
    average_guesses DECIMAL(3,2),
    best_score INTEGER,

    -- Guess distribution as JSON
    distribution JSONB DEFAULT '{}',

    -- Competitive stats
    is_winner BOOLEAN DEFAULT FALSE,

    -- Cache management
    last_updated TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_user_period UNIQUE(user_id, period_type, period_year, period_value)
);

-- Create indexes for cache table
CREATE INDEX IF NOT EXISTS stats_cache_user_idx ON user_stats_cache(user_id);
CREATE INDEX IF NOT EXISTS stats_cache_type_idx ON user_stats_cache(period_type);
CREATE INDEX IF NOT EXISTS stats_cache_updated_idx ON user_stats_cache(last_updated);

-- ==========================================
-- ROW LEVEL SECURITY (Optional)
-- Uncomment if you want to use Supabase Auth
-- ==========================================

-- -- Enable RLS on tables
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE wordle_words ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scores ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_stats_cache ENABLE ROW LEVEL SECURITY;

-- -- Allow all authenticated users to read all data
-- CREATE POLICY "Public read access" ON users FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON wordle_words FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON scores FOR SELECT USING (true);
-- CREATE POLICY "Public read access" ON user_stats_cache FOR SELECT USING (true);

-- -- Users can only insert their own scores
-- CREATE POLICY "Users can insert own scores" ON scores
--     FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- -- Prevent score updates and deletions (immutability)
-- CREATE POLICY "Scores cannot be updated" ON scores FOR UPDATE USING (false);
-- CREATE POLICY "Scores cannot be deleted" ON scores FOR DELETE USING (false);

-- ==========================================
-- SAMPLE QUERIES
-- ==========================================

-- Weekly average for a user (Sunday-Saturday)
-- SELECT AVG(s.guesses) as avg_score, COUNT(*) as games_played
-- FROM scores s
-- JOIN wordle_words w ON s.wordle_word_id = w.id
-- WHERE s.user_id = 'user-uuid-here'
--   AND w.game_date >= date_trunc('week', CURRENT_DATE)
--   AND w.game_date < date_trunc('week', CURRENT_DATE) + INTERVAL '1 week';

-- Most 2's scored by each user
-- SELECT u.name, COUNT(*) as two_count
-- FROM scores s
-- JOIN users u ON s.user_id = u.id
-- WHERE s.guesses = 2
-- GROUP BY u.id, u.name
-- ORDER BY two_count DESC;

-- Best day of week for a user
-- SELECT EXTRACT(DOW FROM w.game_date) as day_of_week,
--        TO_CHAR(w.game_date, 'Day') as day_name,
--        AVG(s.guesses) as avg_score,
--        COUNT(*) as games_played
-- FROM scores s
-- JOIN wordle_words w ON s.wordle_word_id = w.id
-- WHERE s.user_id = 'user-uuid-here'
-- GROUP BY EXTRACT(DOW FROM w.game_date), TO_CHAR(w.game_date, 'Day')
-- ORDER BY avg_score ASC;

-- Yearly statistics
-- SELECT EXTRACT(YEAR FROM w.game_date) as year,
--        COUNT(*) as games_played,
--        AVG(s.guesses) as avg_score,
--        SUM(CASE WHEN s.guesses < 7 THEN 1 ELSE 0 END) as games_solved,
--        SUM(CASE WHEN s.guesses = 7 THEN 1 ELSE 0 END) as games_failed
-- FROM scores s
-- JOIN wordle_words w ON s.wordle_word_id = w.id
-- WHERE s.user_id = 'user-uuid-here'
-- GROUP BY EXTRACT(YEAR FROM w.game_date)
-- ORDER BY year DESC;