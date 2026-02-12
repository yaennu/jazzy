-- Auto-create public.users row when a new auth user signs up.
-- Reads "name" from user metadata passed via signUp() options.
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

-- Add unsubscribe token for email unsubscribe links
ALTER TABLE users ADD COLUMN unsubscribe_token UUID DEFAULT gen_random_uuid();
UPDATE users SET unsubscribe_token = gen_random_uuid() WHERE unsubscribe_token IS NULL;
ALTER TABLE users ALTER COLUMN unsubscribe_token SET NOT NULL;
