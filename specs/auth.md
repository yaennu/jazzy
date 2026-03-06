# Feature: User Authentication

Users can register, log in, and manage their accounts via Supabase Auth with email/password.

## Behavior: Registration

New users can create an account with name, email, and password.

- Given a visitor is on the registration page
- When they submit the registration form with name, email, and password:
  - Then a Supabase Auth user is created with the name stored in `user_metadata`
  - Then a database trigger creates a corresponding row in `public.users` with `subscription_status = 'active'`
  - Then a confirmation email is sent to the provided address
  - Then the page shows a "Check your email" message with the submitted email address

## Behavior: Duplicate registration

Attempting to register with an existing email shows an error.

- Given a user already exists with email "user@example.com"
- When a visitor tries to register with the same email:
  - Then the form displays "An account with this email already exists."

## Behavior: Email confirmation

Users must confirm their email before they can fully use their account.

- Given a user has registered but not confirmed their email
- When they click the confirmation link in the email:
  - Then the OTP is verified via `/auth/confirm` route
  - Then a welcome recommendation email is sent with the first album
  - Then the user is redirected to `/settings`

## Behavior: Login

Registered users can log in with email and password.

- Given a user is on the login page
- When they submit valid credentials:
  - Then they are redirected to `/settings`
- When they submit invalid credentials:
  - Then an error message is displayed

## Behavior: Login page structure

The login page contains the expected form elements.

- Given a visitor navigates to `/login`
- Then the page displays a "Login" heading
- Then the page displays email and password input fields
- Then the page displays a "Login" submit button
- Then the page displays a "Forgot password?" link to `/forgot-password`
- Then the page displays a "Register" link to `/register`

## Behavior: Logout

Authenticated users can log out.

- Given a user is logged in and on the settings page
- When they click the "Logout" button:
  - Then the Supabase session is ended
  - Then they are redirected to `/login`

## Behavior: Password reset

Users can reset their password via email.

- Given a user requests a password reset
- When they click the reset link in the email:
  - Then the PKCE auth code is exchanged for a session via `/auth/confirm`
  - Then they are redirected to the password update page

## Behavior: Account deletion

Users can permanently delete their account.

- Given a user is on the settings page
- When they click "Delete Account" and confirm:
  - Then the `delete_account()` RPC function is called
  - Then the user's row in `public.users` is deleted (cascading to `recommendations`)
  - Then the user's row in `auth.users` is deleted
  - Then the session is ended and they are redirected to `/login`

## Behavior: Unsubscribe via email link

Users can unsubscribe without logging in using a token link in emails.

- Given a user clicks the unsubscribe link in a recommendation email
- When the `unsubscribe_by_token` RPC is called with their token:
  - Then their `subscription_status` is set to `'inactive'`
  - Then if the token is invalid, `'invalid_token'` is returned
  - Then if already unsubscribed, `'already_unsubscribed'` is returned
