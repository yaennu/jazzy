export interface WelcomeAlbum {
    title: string
    artist: string
    release_year?: number | null
    cover_image_url?: string | null
    streaming_link_spotify?: string | null
    streaming_link_apple?: string | null
    album_summary?: string | null
    artist_summary?: string | null
}

function renderSummaries(albumSummary?: string | null, artistSummary?: string | null): string {
    if (!albumSummary && !artistSummary) return ''

    let inner = ''
    if (albumSummary) {
        inner += `
                <p style="margin: 0 0 8px; color: #18181b; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">About this album</p>
                <p style="margin: 0${artistSummary ? ' 0 20px' : ''}; color: #52525b; font-size: 14px; line-height: 1.7;">${albumSummary}</p>`
    }
    if (artistSummary) {
        inner += `
                <p style="margin: 0 0 8px; color: #18181b; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">About the artist</p>
                <p style="margin: 0; color: #52525b; font-size: 14px; line-height: 1.7;">${artistSummary}</p>`
    }

    return `
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 24px;">
                <tr>
                  <td style="padding: 20px 24px; background-color: #fafafa; border-radius: 8px; border-left: 3px solid #e4e4e7;">
                    ${inner}
                  </td>
                </tr>
              </table>`
}

export function renderWelcomeEmail(userName: string, album: WelcomeAlbum, unsubscribeUrl?: string): string {
    const { title, artist, release_year, cover_image_url, streaming_link_spotify, streaming_link_apple, album_summary, artist_summary } = album
    const yearText = release_year ? ` (${release_year})` : ''

    let streamingButtons = ''
    if (streaming_link_spotify || streaming_link_apple) {
        let buttons = ''
        if (streaming_link_spotify) {
            buttons += `
                    <a href="${streaming_link_spotify}" class="streaming-btn" style="display: inline-block; background-color: #1DB954; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 12px 24px; border-radius: 8px; margin: 6px; min-width: 160px; box-sizing: border-box; text-align: center;">
                      Listen on Spotify
                    </a>`
        }
        if (streaming_link_apple) {
            buttons += `
                    <a href="${streaming_link_apple}" class="streaming-btn" style="display: inline-block; background-color: #FC3C44; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: 600; padding: 12px 24px; border-radius: 8px; margin: 6px; min-width: 160px; box-sizing: border-box; text-align: center;">
                      Listen on Apple Music
                    </a>`
        }
        streamingButtons = `
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" class="streaming-td" style="padding-top: 24px;">
                    ${buttons}
                  </td>
                </tr>
              </table>`
    }

    const coverRow = cover_image_url
        ? `<tr class="album-cover"><td style="padding: 24px 24px 0; text-align: center;"><img src="${cover_image_url}" alt="${title} album cover" width="260" style="display: block; margin: 0 auto; border-radius: 8px; max-width: 100%; height: auto;" /></td></tr>`
        : ''

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your First Jazz Pick</title>
  <style>
    @media only screen and (max-width: 600px) {
      .email-container { width: 100% !important; border-radius: 0 !important; }
      .email-header-td { padding: 24px !important; }
      .email-body-td { padding: 24px !important; }
      .email-footer-td { padding: 16px 24px !important; }
      .album-cover img { width: 100% !important; max-width: 260px !important; }
      .streaming-btn { display: block !important; margin: 6px auto !important; min-width: 200px !important; width: 80% !important; max-width: 260px !important; }
      .streaming-td { padding-top: 16px !important; }
    }
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #ffffff; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" class="email-container" style="max-width: 480px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
          <!-- Header -->
          <tr>
            <td class="email-header-td" style="background-color: #18181b; padding: 32px 40px; text-align: center;">
              <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">Jazzy</h1>
              <p style="margin: 8px 0 0; color: #a1a1aa; font-size: 14px;">Your jazz album recommendations</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td class="email-body-td" style="padding: 40px;">
              <h2 style="margin: 0 0 16px; color: #18181b; font-size: 22px; font-weight: 600;">Welcome, ${userName}!</h2>
              <p style="margin: 0 0 24px; color: #52525b; font-size: 15px; line-height: 1.6;">
                Your account is confirmed. To kick things off, here's your first jazz pick — give it a listen and let the music take you somewhere new.
              </p>
              <!-- Album Card -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border-radius: 8px; border: 1px solid #e4e4e7;">
                ${coverRow}
                <tr>
                  <td style="padding: 24px; text-align: center;">
                    <p style="margin: 0 0 4px; color: #18181b; font-size: 20px; font-weight: 700;">${title}</p>
                    <p style="margin: 0; color: #52525b; font-size: 16px;">${artist}${yearText}</p>
                  </td>
                </tr>
              </table>
              ${streamingButtons}
              ${renderSummaries(album_summary, artist_summary)}
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td class="email-footer-td" style="padding: 24px 40px; border-top: 1px solid #e4e4e7; text-align: center;">
              <p style="margin: 0; color: #a1a1aa; font-size: 12px;">Jazzy &mdash; Discover jazz, one album at a time.</p>
              ${unsubscribeUrl ? `<p style="margin: 8px 0 0; font-size: 12px;"><a href="${unsubscribeUrl}" style="color: #a1a1aa; text-decoration: underline;">Unsubscribe</a></p>` : ''}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`
}
