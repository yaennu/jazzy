# jazzy
A simple web app where users can subscribe to receive periodic jazz album recommendations via email.

## Getting Started

### Prerequisites

- Node.js 18+
- npm
- Python 3.13+ (for backend scripts)

### Install Dependencies

```bash
npm install
```

### Frontend

```bash
cd packages/frontend
npm run dev
```

The app will be available at `http://localhost:3000`.

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
   source venv/bin/activate
   pip install -r requirements.txt
   python src/main.py
   ```

On startup, the backend checks if the `albums` table is empty. If so, it seeds it from `data/albums.csv`. If the table already has data, it skips seeding.

### VS Code Tasks

You can also start the services directly from VS Code:

1. Open the Command Palette (`Cmd+Shift+P`)
2. Select **Tasks: Run Task**
3. Choose one of:
   - **Frontend: Dev Server** — starts the Next.js dev server
   - **Backend: Activate & Run** — activates the venv, installs deps, and seeds the database if empty
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
3. The workflow checks if the `albums` table is empty and seeds it from `data/albums.csv`

### Email Recommendations (GitHub Actions)

Album recommendations are sent automatically via a scheduled GitHub Actions workflow using [Resend](https://resend.com).

1. Sign up at [resend.com](https://resend.com) and create an API key
2. Verify a sending domain (or use the test domain for development)
3. Add the `RESEND_API_KEY` secret in **Settings > Secrets and variables > Actions**
4. The **Send Recommendations** workflow runs daily at 04:00 UTC
5. It can also be triggered manually from **Actions > Send Recommendations > Run workflow**

The script checks each user's `newsletter_frequency` preference (daily/weekly/monthly) and sends a random unsent album recommendation to eligible users. When all albums have been sent, the recommendation history resets and starts over from the beginning.

## Backend Scripts

### Add Streaming Links

This script looks up Spotify and Apple Music links for albums in the database that are missing streaming links, using the Spotify Web API and iTunes Search API.

1.  Navigate to the backend package directory:
    ```bash
    cd packages/backend
    ```
2.  Activate the Python virtual environment:
    ```bash
    source venv/bin/activate
    ```
3.  Ensure your `.env` file contains the required credentials (see `.env.example` for `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and Supabase credentials)
4.  Run the script:
    ```bash
    python src/scripts/add_streaming_links.py
    ```

### Add Album Covers

This script looks up album cover art for albums that have an Apple Music streaming link but no cover image, using the iTunes Search API.

1.  Navigate to the backend package directory:
    ```bash
    cd packages/backend
    ```
2.  Activate the Python virtual environment:
    ```bash
    source venv/bin/activate
    ```
3.  Run the script:
    ```bash
    python src/scripts/add_album_covers.py
    ```

### Extract Album Data

This script extracts album information from HEIC photos in the `data/heic-images/` directory using OCR and outputs to `data/albums.csv`.

1.  Navigate to the backend package directory:
    ```bash
    cd packages/backend
    ```
2.  Activate the Python virtual environment:
    ```bash
    source venv/bin/activate
    ```
3.  Run the script:
    ```bash
    python src/scripts/extract_album_data.py
    ```
    