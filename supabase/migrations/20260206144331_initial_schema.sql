CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT,
    subscription_status VARCHAR(50) NOT NULL,
    is_email_verified BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    newsletter_frequency VARCHAR(50) DEFAULT 'weekly'
);

CREATE TABLE albums (
    album_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    release_year INT,
    cover_image_url TEXT,
    streaming_link_spotify TEXT,
    streaming_link_apple TEXT
);

CREATE TABLE recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    album_id UUID NOT NULL REFERENCES albums(album_id) ON DELETE CASCADE,
    sent_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
