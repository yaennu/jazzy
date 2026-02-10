"""
HTML email template for jazz album recommendations.
Matches the visual style of the signup confirmation email.
"""


def render_recommendation_email(user_name: str, album: dict) -> str:
    title = album.get("title", "Unknown Album")
    artist = album.get("artist", "Unknown Artist")
    release_year = album.get("release_year")
    spotify_link = album.get("streaming_link_spotify")
    apple_link = album.get("streaming_link_apple")

    year_text = f" ({release_year})" if release_year else ""

    streaming_buttons = ""
    if spotify_link or apple_link:
        buttons = ""
        if spotify_link:
            buttons += f'''
                    <a href="{spotify_link}" style="display: inline-block; background-color: #1DB954; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 10px 24px; border-radius: 8px; margin: 0 6px;">
                      Listen on Spotify
                    </a>'''
        if apple_link:
            buttons += f'''
                    <a href="{apple_link}" style="display: inline-block; background-color: #FC3C44; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 10px 24px; border-radius: 8px; margin: 0 6px;">
                      Listen on Apple Music
                    </a>'''
        streaming_buttons = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-top: 24px;">
                    {buttons}
                  </td>
                </tr>
              </table>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Jazz Recommendation</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f5; padding: 40px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td style="background-color: #18181b; padding: 32px 40px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Jazzy</h1>
              <p style="margin: 8px 0 0; color: #a1a1aa; font-size: 14px;">Your jazz album recommendations</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding: 40px;">
              <h2 style="margin: 0 0 16px; color: #18181b; font-size: 22px; font-weight: 600;">Hey {user_name}!</h2>
              <p style="margin: 0 0 24px; color: #52525b; font-size: 15px; line-height: 1.6;">
                We picked a jazz album just for you. Give it a listen and let the music take you somewhere new.
              </p>
              <!-- Album Card -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f5; border-radius: 8px;">
                <tr>
                  <td style="padding: 24px; text-align: center;">
                    <p style="margin: 0 0 4px; color: #18181b; font-size: 20px; font-weight: 700;">{title}</p>
                    <p style="margin: 0; color: #52525b; font-size: 16px;">{artist}{year_text}</p>
                  </td>
                </tr>
              </table>
              {streaming_buttons}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 24px 40px; border-top: 1px solid #e4e4e7; text-align: center;">
              <p style="margin: 0; color: #a1a1aa; font-size: 12px;">Jazzy &mdash; Discover jazz, one album at a time.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>'''
