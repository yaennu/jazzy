# jazzy
A simple web app where users can subscribe to receive periodic jazz album recommendations via email.

**Live at [jazzy.yaennu.ch](https://jazzy.yaennu.ch)**

## Getting Started

### Prerequisites

- Node.js 18+
- npm
- [uv](https://docs.astral.sh/uv/) (for backend scripts)

### Install Dependencies

```bash
npm install
```

### Frontend

```bash
cd packages/frontend
npm run dev
```

The app will be available at `http://localhost:3001`.

### Backend

1. Copy `packages/backend/.env` and set your Supabase credentials:
   ```
   SUPABASE_URL=https://<your-project-ref>.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
   ```
   The service role key is found in your Supabase dashboard under **Settings > API**.

2. Start the backend:
   ```bash
   cd packages/backend
   uv run python src/main.py
   ```

On startup, the backend checks if the `albums` table is empty. If so, it runs the full seeding pipeline: extracting album data from images, looking up streaming links, fetching cover art, and generating LLM summaries. If the table already has data, it skips seeding.

### VS Code Tasks

You can also start the services directly from VS Code:

1. Open the Command Palette (`Cmd+Shift+P`)
2. Select **Tasks: Run Task**
3. Choose one of:
   - **Frontend: Dev Server** — starts the Next.js dev server
   - **Backend: Activate & Run** — installs deps via uv and seeds the database if empty
   - **Start All** — runs both in parallel

## Supabase

Install the CLI (if you haven't already)

```
npm install supabase --save-dev
```

Log in to your Supabase account
```
npx supabase login
```

Link your local project to your remote Supabase project
Find your [project-ref] in your Supabase project's URL (e.g., https://app.supabase.com/project/[project-ID])
```
npx supabase link --project-ref [your-project-ID]
```

Reset the remote database and apply all migrations
```
npx supabase db reset --linked
```

## Deployment

### Frontend (Vercel)

1. Import the repository on [vercel.com](https://vercel.com)
2. Set the **Root Directory** to `packages/frontend`
3. Add environment variables in the Vercel dashboard:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Deploy — Vercel auto-detects Next.js and builds on every push

### Database Seeding (GitHub Actions)

1. Add repository secrets in **Settings > Secrets and variables > Actions**:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
2. Go to **Actions > Seed Database > Run workflow**
3. The workflow checks if the `albums` table is empty and runs the full seeding pipeline (extraction, streaming links, covers, summaries)

### Email Recommendations (GitHub Actions)

Album recommendations are sent automatically via a scheduled GitHub Actions workflow using [Resend](https://resend.com).

1. Sign up at [resend.com](https://resend.com) and create an API key
2. Verify a sending domain (or use the test domain for development)
3. Add the `RESEND_API_KEY` and `FROM_EMAIL` (e.g., `Jazzy <noreply@jazzy.yaennu.ch>`) secrets in **Settings > Secrets and variables > Actions**
4. The **Send Recommendations** workflow runs daily at 04:00 UTC
5. It can also be triggered manually from **Actions > Send Recommendations > Run workflow**

The script checks each user's `newsletter_frequency` preference (daily/weekly/monthly) and sends a random unsent album recommendation to eligible users. When all albums have been sent, the recommendation history resets and starts over from the beginning.

## Backend Scripts

All scripts are run from `packages/backend/`. The seeding script (`main.py`) runs them all in sequence automatically, but they can also be run individually:

### Extract Album Data

Extracts album information from PNG images in `data/png-images/` using Google Gemini 2.0 Flash vision model and inserts records into the database.

```bash
uv run python src/scripts/extract_album_data.py
```

Requires `GEMINI_API_KEY` in `.env.local`.

### Add Streaming Links

Looks up Spotify and Apple Music links for albums missing streaming links, using the Spotify Web API and iTunes Search API. Uses a multi-strategy approach including an Apple Music → Spotify UPC bridge for higher-confidence matching.

```bash
uv run python src/scripts/add_streaming_links.py
```

Requires `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in `.env.local` (see `.env.example`).

### Add Album Covers

Looks up album cover art for albums that have an Apple Music link but no cover image, using the iTunes Search API.

```bash
uv run python src/scripts/add_album_covers.py
```

### Add Album Summaries

Generates artist and album summaries using the Perplexity API (search-augmented LLM) with Wikipedia links.

```bash
uv run python src/scripts/add_album_summaries.py
```

Requires `PERPLEXITY_API_KEY` in `.env.local`.

### Verify Album Records

Verifies the consistency of all album records in the database (title, artist, release year, label, summaries, streaming links, etc.) using the Claude Agent SDK. Runs albums in parallel batches and writes findings to an xlsx file in `packages/backend/output/`.

```bash
cd packages/backend
uv run python src/verify_album_records.py
```

Requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Uses Claude Code's authentication — no separate `ANTHROPIC_API_KEY` needed.
    