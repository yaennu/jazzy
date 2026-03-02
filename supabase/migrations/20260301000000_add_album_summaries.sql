-- Add LLM-generated summary columns to albums table
ALTER TABLE albums
    ADD COLUMN artist_summary TEXT,
    ADD COLUMN album_summary TEXT;
