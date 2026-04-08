-- Add default_model column to channels table
ALTER TABLE channels ADD COLUMN IF NOT EXISTS default_model TEXT DEFAULT 'gemini-2.5-flash';
