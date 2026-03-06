# Feature: Email Recommendations

Jazz album recommendations are sent to users via email on a schedule determined by their newsletter frequency preference.

## Behavior: Frequency eligibility

The system determines which frequency tiers are eligible each day.

- Given the recommendation script runs daily at 04:00 UTC
- When it checks the current date:
  - Then `daily` subscribers are always eligible
  - Then `weekly` subscribers are eligible only on Mondays (weekday == 0)
  - Then `monthly` subscribers are eligible only on the 1st of the month

## Behavior: User eligibility

Only active, subscribed users with a matching frequency receive emails.

- Given a user exists in the `users` table
- When the system checks eligibility:
  - Then the user must have `subscription_status = 'active'`
  - Then the user's `newsletter_frequency` must match one of today's eligible frequencies

## Behavior: Album selection (next unsent album)

Each user receives the next album they haven't been sent yet, ordered by `calendar_order`.

- Given a user has been sent some albums already (entries in `recommendations` table)
- When the system selects the next album:
  - Then it filters out all albums already in the user's recommendation history
  - Then it sorts remaining albums by `calendar_order` ascending (NULLs last)
  - Then it picks the first unsent album whose `calendar_order` is greater than the last sent album's `calendar_order`
  - Then if no such album exists (wrap-around), it picks the first unsent album in sequence

## Behavior: History reset

When all albums have been sent to a user, the recommendation history resets.

- Given a user has been sent every album in the `albums` table
- When the system tries to find an unsent album:
  - Then it deletes all of that user's entries from the `recommendations` table
  - Then it treats all albums as unsent and picks the first one by `calendar_order`

## Behavior: Email delivery

Each eligible user receives one email per run containing a single album recommendation.

- Given an eligible user and a selected album
- When the email is sent:
  - Then the email subject contains the album title and artist
  - Then the email includes an unsubscribe link using the user's `unsubscribe_token`
  - Then a row is inserted into `recommendations` with `user_id` and `album_id`
  - Then the `sent_date` is recorded automatically

## Behavior: No albums available

If the albums table is empty, no emails are sent.

- Given the `albums` table contains no rows
- When the system tries to select an album for a user:
  - Then it returns no album and skips that user
