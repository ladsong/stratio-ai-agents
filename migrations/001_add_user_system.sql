-- Migration: Add user-centric conversation system
-- This adds users, user_contacts, and admin_commands tables
-- Also adds user_id, channel, contact_id to threads table

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    system_prompt TEXT,
    meta JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create user_contacts table
CREATE TABLE IF NOT EXISTS user_contacts (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    contact_id VARCHAR(255) NOT NULL,
    meta JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(channel, contact_id)
);

-- Create admin_commands table
CREATE TABLE IF NOT EXISTS admin_commands (
    id VARCHAR(255) PRIMARY KEY,
    admin_user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL,
    params JSONB,
    result TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Add user-related columns to threads table
ALTER TABLE threads ADD COLUMN IF NOT EXISTS user_id VARCHAR(255) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE threads ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE threads ADD COLUMN IF NOT EXISTS contact_id VARCHAR(255);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_contacts_user_id ON user_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_contacts_channel_contact ON user_contacts(channel, contact_id);
CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);
CREATE INDEX IF NOT EXISTS idx_threads_channel_contact ON threads(channel, contact_id);
CREATE INDEX IF NOT EXISTS idx_admin_commands_admin_user_id ON admin_commands(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_commands_created_at ON admin_commands(created_at DESC);

-- Create unique index on user_contacts to prevent duplicate contacts
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_contacts_unique ON user_contacts(channel, contact_id);
