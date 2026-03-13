"""
Send jazz album recommendations to eligible users via Resend.
Runs daily via GitHub Actions cron. Checks each user's newsletter_frequency
to decide who gets an email today.
"""

import os
import sys
from datetime import datetime, timezone

import resend
from dotenv import load_dotenv
from supabase import create_client, Client

from email_template import render_recommendation_email

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

FROM_EMAIL = os.environ.get("FROM_EMAIL", "Jazzy <onboarding@resend.dev>")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")


def get_supabase_client() -> Client:
    load_dotenv(os.path.join(BACKEND_ROOT, ".env.local"))
    if os.environ.get("PRODUCTION") == "True":
        load_dotenv(os.path.join(BACKEND_ROOT, ".env.production"), override=True)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.")
        sys.exit(1)
    return create_client(url, key)


def init_resend() -> None:
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("Error: RESEND_API_KEY must be set.")
        sys.exit(1)
    resend.api_key = api_key


def get_eligible_frequencies() -> list[str]:
    """Return which newsletter frequencies should be sent today."""
    now = datetime.now(timezone.utc)
    frequencies = ["daily"]

    if now.weekday() == 0:  # Monday
        frequencies.append("weekly")

    if now.day == 1:
        frequencies.append("monthly")

    return frequencies


def get_eligible_users(client: Client) -> list[dict]:
    """Query users with active subscriptions whose frequency matches today."""
    frequencies = get_eligible_frequencies()
    print(f"Eligible frequencies today: {frequencies}")

    response = (
        client.table("users")
        .select("user_id, email, name, newsletter_frequency, unsubscribe_token")
        .eq("subscription_status", "active")
        .in_("newsletter_frequency", frequencies)
        .execute()
    )
    return response.data


def _get_last_sent_order(client: Client, user_id: str) -> int | None:
    """Get the calendar_order of the most recently sent album for a user."""
    response = (
        client.table("recommendations")
        .select("album_id, albums(calendar_order)")
        .eq("user_id", user_id)
        .order("sent_date", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    album_data = response.data[0].get("albums")
    if album_data:
        return album_data.get("calendar_order")
    return None


def get_unsent_album(client: Client, user_id: str) -> dict | None:
    """Pick the next album in calendar_order that hasn't been sent to this user."""
    # Get album IDs already sent to this user
    sent_response = (
        client.table("recommendations")
        .select("album_id")
        .eq("user_id", user_id)
        .execute()
    )
    sent_ids = [r["album_id"] for r in sent_response.data]

    # Get all albums ordered by calendar_order
    albums_response = client.table("albums").select("*").execute()
    all_albums = albums_response.data

    # Filter out already-sent albums
    unsent = [a for a in all_albums if a["album_id"] not in sent_ids]

    if not unsent:
        # All albums sent — clear history and start over
        client.table("recommendations").delete().eq("user_id", user_id).execute()
        unsent = all_albums

    if not unsent:
        return None

    # Sort: albums with calendar_order first (ascending), NULLs last
    unsent.sort(key=lambda a: (a.get("calendar_order") is None, a.get("calendar_order") or 0))

    last_order = _get_last_sent_order(client, user_id)

    if last_order is not None:
        # Find the first unsent album with calendar_order > last_order
        for album in unsent:
            order = album.get("calendar_order")
            if order is not None and order > last_order:
                return album

    # No previous recommendation, or wrap-around: return the first in sequence
    return unsent[0]


def send_email(user: dict, album: dict) -> bool:
    """Send a recommendation email via Resend. Returns True on success."""
    unsubscribe_url = f"{FRONTEND_URL}/unsubscribe?token={user['unsubscribe_token']}"
    html = render_recommendation_email(user["name"], album, unsubscribe_url)

    try:
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [user["email"]],
            "subject": f"Your jazz pick: {album['title']} by {album['artist']}",
            "html": html,
        })
        return True
    except Exception as e:
        print(f"  Failed to send to {user['email']}: {e}")
        return False


def record_recommendation(client: Client, user_id: str, album_id: str) -> None:
    """Insert a row into the recommendations table."""
    client.table("recommendations").insert({
        "user_id": user_id,
        "album_id": album_id,
    }).execute()


def main():
    print("Starting recommendation emails...")

    client = get_supabase_client()
    init_resend()

    users = get_eligible_users(client)
    print(f"Found {len(users)} eligible user(s).")

    sent_count = 0
    skip_count = 0

    for user in users:
        album = get_unsent_album(client, user["user_id"])

        if album is None:
            print(f"  {user['email']}: no unsent albums left, skipping.")
            skip_count += 1
            continue

        print(f"  {user['email']}: sending '{album['title']}' by {album['artist']}...")

        if send_email(user, album):
            record_recommendation(client, user["user_id"], album["album_id"])
            sent_count += 1

    print(f"\nDone. Sent: {sent_count}, Skipped: {skip_count}, Failed: {len(users) - sent_count - skip_count}")


if __name__ == "__main__":
    main()
