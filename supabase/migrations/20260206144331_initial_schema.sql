-- ============================================================
-- Tables
-- ============================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT,
    subscription_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    newsletter_frequency VARCHAR(50) DEFAULT 'weekly',
    unsubscribe_token UUID NOT NULL DEFAULT gen_random_uuid()
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

-- ============================================================
-- Auth trigger: auto-create public.users row on signup
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (user_id, email, name, subscription_status)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', 'User'),
    'active'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- Row Level Security
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE albums ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;

-- USERS policies
CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow auth trigger to create users"
  ON users FOR INSERT
  WITH CHECK (true);

-- ALBUMS policies
CREATE POLICY "Authenticated users can read albums"
  ON albums FOR SELECT
  TO authenticated
  USING (true);

-- RECOMMENDATIONS policies
CREATE POLICY "Users can read own recommendations"
  ON recommendations FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

-- ============================================================
-- RPC function for unauthenticated unsubscribe via email link
-- ============================================================

CREATE OR REPLACE FUNCTION public.unsubscribe_by_token(p_token UUID)
RETURNS TEXT AS $$
DECLARE
  v_status TEXT;
BEGIN
  SELECT subscription_status INTO v_status
  FROM public.users
  WHERE unsubscribe_token = p_token;

  IF v_status IS NULL THEN
    RETURN 'invalid_token';
  END IF;

  IF v_status = 'inactive' THEN
    RETURN 'already_unsubscribed';
  END IF;

  UPDATE public.users
  SET subscription_status = 'inactive'
  WHERE unsubscribe_token = p_token;

  RETURN 'success';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- Schema grants for PostgREST (required after db reset)
-- ============================================================

GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO anon, authenticated;
