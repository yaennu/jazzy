# jazzy
A project about a simple web app where the user can subscribe for a periodically jazz album recomendation via mail.

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

## kilocode

copy mcp.example.json for GitHub MCP server access:
```
cp mcp.example.json mcp.json;
```
