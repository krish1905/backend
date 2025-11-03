-- Financial P2P Application Database Schema
-- Run this in your Supabase SQL Editor to create the necessary tables

-- ============================================================================
-- Create ENUM Types
-- ============================================================================

CREATE TYPE IF NOT EXISTS transaction_status AS ENUM ('pending', 'completed', 'failed');
CREATE TYPE IF NOT EXISTS transaction_category AS ENUM ('transfer', 'payment', 'refund');


-- ============================================================================
-- Users Table (extends Supabase auth.users)
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    full_name VARCHAR,
    balance NUMERIC(10, 2) DEFAULT 1000.00 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);


-- ============================================================================
-- Transactions Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    to_user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    description VARCHAR(500),
    status transaction_status DEFAULT 'pending' NOT NULL,
    category transaction_category DEFAULT 'transfer' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Indexes for transactions table
CREATE INDEX IF NOT EXISTS idx_transactions_from_user ON transactions(from_user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_to_user ON transactions(to_user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);


-- ============================================================================
-- Triggers for updated_at timestamp
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

-- Users table policies
-- Users can view all users (for searching recipients)
CREATE POLICY "Users can view all users"
    ON users FOR SELECT
    USING (true);

-- Users can update only their own profile
CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- Transactions table policies
-- Users can view their own transactions (sent or received)
CREATE POLICY "Users can view own transactions"
    ON transactions FOR SELECT
    USING (auth.uid() = from_user_id OR auth.uid() = to_user_id);

-- Users can insert transactions where they are the sender
CREATE POLICY "Users can create transactions"
    ON transactions FOR INSERT
    WITH CHECK (auth.uid() = from_user_id);


-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE users IS 'User profiles with balance information';
COMMENT ON TABLE transactions IS 'P2P transaction records';

COMMENT ON COLUMN users.id IS 'References Supabase auth.users.id';
COMMENT ON COLUMN users.balance IS 'Current user balance in dollars';
COMMENT ON COLUMN transactions.status IS 'Transaction status: pending, completed, or failed';
COMMENT ON COLUMN transactions.category IS 'Transaction type: transfer, payment, or refund';

