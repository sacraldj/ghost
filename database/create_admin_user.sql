-- Simple script to create/update admin user
-- Use this if you already have the users table

INSERT INTO users (email, name, password_hash, role, is_active, email_verified, created_at, updated_at)
VALUES (
  'admin@ghost.com',
  'GHOST Admin',
  '$2b$12$Y5rupWCjTGYXiQe99yETbOOytHpzGY3iTHnGoWjP7qjgJN3OT0B7.',
  'admin',
  true,
  true,
  NOW(),
  NOW()
) ON CONFLICT (email) DO UPDATE SET
  name = EXCLUDED.name,
  password_hash = EXCLUDED.password_hash,
  role = EXCLUDED.role,
  is_active = EXCLUDED.is_active,
  email_verified = EXCLUDED.email_verified,
  updated_at = NOW();

-- Verify the admin user was created
SELECT 
  email, 
  name, 
  role, 
  is_active, 
  email_verified,
  created_at
FROM users 
WHERE email = 'admin@ghost.com';
