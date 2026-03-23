-- Remove unused password_hash column from users table.
-- Passwords are managed entirely by Supabase Auth (auth.users);
-- this column was never populated and storing it violates data minimization.

ALTER TABLE users DROP COLUMN IF EXISTS password_hash;
