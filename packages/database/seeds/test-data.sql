-- Seed data for the database

-- Generate UUIDs for users
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
DO $$
DECLARE
    user1_uuid UUID := uuid_generate_v4();
    user2_uuid UUID := uuid_generate_v4();
    user3_uuid UUID := uuid_generate_v4();
    album1_uuid UUID := uuid_generate_v4();
    album2_uuid UUID := uuid_generate_v4();
    album3_uuid UUID := uuid_generate_v4();
BEGIN
    -- Insert test users
    INSERT INTO users (user_id, email, name, password_hash, subscription_status)
    VALUES
        (user1_uuid, 'user1@example.com', 'User One', 'hash1', 'active'),
        (user2_uuid, 'user2@example.com', 'User Two', 'hash2', 'inactive'),
        (user3_uuid, 'user3@example.com', 'User Three', 'hash3', 'active');

    -- Insert test albums
    INSERT INTO albums (album_id, title, artist, release_year)
    VALUES
        (album1_uuid, 'Album One', 'Artist A', 2023),
        (album2_uuid, 'Album Two', 'Artist B', 2022),
        (album3_uuid, 'Album Three', 'Artist C', 2021);

    -- Insert test recommendations
    INSERT INTO recommendations (user_id, album_id)
    VALUES
        (user1_uuid, album1_uuid),
        (user2_uuid, album2_uuid),
        (user3_uuid, album3_uuid);
END $$;
