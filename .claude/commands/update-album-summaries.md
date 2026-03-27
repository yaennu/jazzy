# Update Album Summaries

Generate and write artist and album summaries for a given album in the production Supabase database (`hnxhjidffyireafbxbew`).

## Instructions

The user will provide one or more album IDs. For each one:

1. Query the production Supabase database for the album's `title`, `artist`, `release_year`, `artist_summary`, and `album_summary`.
2. For any summary that is already set, skip it and do not overwrite.
3. For any summary that is `null`, compose a new one following the style guide below.
4. Present all composed summaries to the user for review and ask for confirmation before writing.
5. On confirmation, write the summaries to the production database via SQL UPDATE.

## Summary Style Guide

- **Length:** 40–60 words each
- **Format:** Plain prose, single line (no newlines, no bullet points, no headings)
- **Links:** Wrap every person, musician, band, record label, album, and record mentioned in an HTML anchor tag `<a href="URL">name</a>` pointing to their Wikipedia page. Only use URLs you are confident exist.
- **Citations:** Do not use `[n]` footnote markers
- **Tone:** Factual and engaging, written for a jazz-literate audience

### Artist summary
Cover the artist's background, musical style, and significance in jazz history.

### Album summary
Cover the album's musical style, recording context, key tracks, and why it matters — or if little is known, write about the artist's general style in relation to this album. Do not repeat biographical details already covered in the artist summary. If the album is a reissue or archival release (e.g. release year is well after the artist's peak activity), mention that context.

## Arguments

`$ARGUMENTS` — one or more album UUIDs, space- or comma-separated. If none provided, ask the user for the album ID(s).
