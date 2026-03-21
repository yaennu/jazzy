"""Verify album records in the Supabase database using the Claude Agent SDK.

Uses Claude Code with the Supabase MCP to fetch all album records, verify
each record's consistency (title, artist, release year, label, summaries,
etc.), and write findings to an xlsx file.
"""

import asyncio
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from pydantic import BaseModel

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


class AlbumFinding(BaseModel):
    album_id: str
    title: str
    artist: str
    is_legitimate: bool
    release_year_correct: bool
    label_correct: bool
    artist_summary_coherent: bool
    album_summary_coherent: bool
    cover_artists_correct: bool
    apple_link_coherent: bool
    issues: str
    confidence: str


class VerificationResults(BaseModel):
    findings: list[AlbumFinding]


VERIFICATION_PROMPT = """\
You are a jazz music expert verifying the accuracy of album records in a database.

Use the Supabase MCP to query ALL records from the "albums" table. Fetch every column:
album_id, title, artist, release_year, label_name, cover_artists,
artist_summary, album_summary, streaming_link_spotify, streaming_link_apple,
cover_image_url, calendar_order, apple_link_is_substitute,
spotify_link_is_substitute, image_filename.

For EACH album record, verify the following:

1. **is_legitimate**: Is this title + artist combination a real, legitimate jazz album?
   Mark false if the album doesn't exist or is clearly wrong.

2. **release_year_correct**: Does the release_year in the database match the actual
   release year of this album? If release_year is NULL, mark as true but note it in issues.

3. **label_correct**: Does the label_name match the actual record label for this album?
   If label_name is NULL, mark as true but note it in issues.

4. **artist_summary_coherent**: Is the artist_summary actually about the correct artist
   and factually reasonable? If NULL, mark as true but note it.

5. **album_summary_coherent**: Is the album_summary actually about the correct album
   and factually reasonable? If NULL, mark as true but note it.

6. **cover_artists_correct**: Are the cover_artists (sidemen/personnel) coherent with
   this album? If NULL, mark as true but note it.

7. **apple_link_coherent**: Check the streaming_link_apple URL text (do NOT visit the URL).
   Apple Music URLs typically contain the artist name, album title, and sometimes a year
   in their path (e.g., "https://music.apple.com/us/album/blue-train/724467923").
   Verify that the text in the URL is coherent with the album's title and artist.
   If the URL contains a different artist or album name, mark as false.
   If streaming_link_apple is NULL, mark as true but note it in issues.
   Also consider apple_link_is_substitute: if true, the link may point to a different
   album by the same artist (which is acceptable but should be noted).

8. **issues**: A free-text description of ALL issues found. Include:
   - Any factual inaccuracies
   - NULL columns that should have values
   - Mismatched data (e.g., wrong year, wrong label)
   - Streaming links that look malformed (not full URLs)
   - Any other inconsistencies
   If no issues, use "No issues found."

9. **confidence**: Your confidence in the verification: "high", "medium", or "low".
   Use "low" if you're unsure about the album's existence or details.

Return the results as structured JSON matching the required schema.
"""


async def verify_albums() -> VerificationResults:
    """Send verification prompt to Claude Code via the Agent SDK."""
    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        allowed_tools=["mcp__supabase__*"],
        permission_mode="bypassPermissions",
        output_format={
            "type": "json_schema",
            "schema": VerificationResults.model_json_schema(),
        },
        max_turns=50,
    )

    result_text = None
    structured_output = None

    print("Starting album verification with Claude Code...")
    print(f"Project root: {PROJECT_ROOT}")

    async for message in query(
        prompt=VERIFICATION_PROMPT,
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"  Claude: {block.text[:200]}")
        elif isinstance(message, ResultMessage):
            print(f"  Status: {message.subtype} (turns: {message.num_turns})")
            if message.total_cost_usd:
                print(f"  Cost: ${message.total_cost_usd:.4f}")
            result_text = message.result
            structured_output = message.structured_output

    if structured_output:
        return VerificationResults.model_validate(structured_output)

    if result_text:
        try:
            data = json.loads(result_text)
            return VerificationResults.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Warning: Could not parse result as JSON: {e}")
            print(f"Raw result (first 500 chars): {result_text[:500]}")

    print("Error: No usable results returned from Claude Code.")
    sys.exit(1)


def write_xlsx(results: VerificationResults, output_path: Path) -> None:
    """Write verification findings to an xlsx file."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Album Verification"

    headers = [
        "Album ID",
        "Title",
        "Artist",
        "Legitimate?",
        "Release Year OK?",
        "Label OK?",
        "Artist Summary OK?",
        "Album Summary OK?",
        "Cover Artists OK?",
        "Apple Link OK?",
        "Issues",
        "Confidence",
    ]

    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    wrap_alignment = Alignment(wrap_text=True, vertical="top")

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font_white
        cell.fill = header_fill

    bool_columns = [4, 5, 6, 7, 8, 9, 10]  # 1-indexed column numbers for boolean fields

    for row_idx, finding in enumerate(results.findings, 2):
        row_data = [
            finding.album_id,
            finding.title,
            finding.artist,
            finding.is_legitimate,
            finding.release_year_correct,
            finding.label_correct,
            finding.artist_summary_coherent,
            finding.album_summary_coherent,
            finding.cover_artists_correct,
            finding.apple_link_coherent,
            finding.issues,
            finding.confidence,
        ]

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if col_idx in bool_columns:
                cell.value = "YES" if value else "NO"
                cell.fill = green_fill if value else red_fill
            if col_idx == 11:  # Issues column
                cell.alignment = wrap_alignment

    # Auto-size columns
    column_widths = {
        "A": 38,   # Album ID (UUID)
        "B": 35,   # Title
        "C": 25,   # Artist
        "D": 13,   # Legitimate?
        "E": 17,   # Release Year OK?
        "F": 12,   # Label OK?
        "G": 19,   # Artist Summary OK?
        "H": 19,   # Album Summary OK?
        "I": 17,   # Cover Artists OK?
        "J": 16,   # Apple Link OK?
        "K": 60,   # Issues
        "L": 13,   # Confidence
    }

    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    # Freeze the header row
    ws.freeze_panes = "A2"

    # Add auto-filter
    ws.auto_filter.ref = f"A1:L{len(results.findings) + 1}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    print(f"Wrote {len(results.findings)} findings to {output_path}")


def print_summary(results: VerificationResults) -> None:
    """Print a summary of the verification results."""
    total = len(results.findings)
    issues_count = sum(1 for f in results.findings if f.issues != "No issues found.")
    illegitimate = sum(1 for f in results.findings if not f.is_legitimate)
    low_confidence = sum(1 for f in results.findings if f.confidence == "low")

    print(f"\n{'=' * 50}")
    print(f"VERIFICATION SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total albums verified: {total}")
    print(f"Albums with issues:    {issues_count}")
    print(f"Illegitimate albums:   {illegitimate}")
    print(f"Low confidence:        {low_confidence}")
    print(f"{'=' * 50}")


async def main() -> None:
    output_path = OUTPUT_DIR / "album_verification.xlsx"

    results = await verify_albums()
    write_xlsx(results, output_path)
    print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
