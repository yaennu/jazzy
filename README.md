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

```bash
cd packages/backend
source venv/bin/activate
pip install -r requirements.txt
```

### VS Code Tasks

You can also start the services directly from VS Code:

1. Open the Command Palette (`Cmd+Shift+P`)
2. Select **Tasks: Run Task**
3. Choose one of:
   - **Frontend: Dev Server** — starts the Next.js dev server
   - **Backend: Activate & Run** — activates the venv and runs the extract script
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

Execute the SQL file on the remote database
```
cat schema.sql | npx supabase db remote set
```

## Backend Scripts

### Extract Album Data

This script extracts album information from photos in the `data/photos` directory and generates a JSON file at `data/albums.json` and a SQL seed file at `supabase/seed.sql`.

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
    