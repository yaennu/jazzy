# CLAUDE.md

## Project Overview

Jazzy is a web application where users subscribe to receive periodic jazz album recommendations via email. It is a monorepo using Supabase (PostgreSQL) as the database backend.

**License:** GPLv3

## Repository Structure

```
jazzy/
├── packages/
│   ├── frontend/          # Next.js 16 (App Router) frontend
│   │   ├── public/        # Static assets
│   │   └── src/
│   │       ├── app/           # Next.js App Router pages & API routes
│   │       ├── components/    # Reusable UI components (incl. shadcn/ui)
│   │       ├── lib/           # Utilities & Supabase client setup
│   │       └── email-templates/ # Email HTML templates
│   └── backend/           # Python backend scripts
│       └── src/
│           ├── main.py        # Album seeding script
│           └── scripts/       # Data extraction utilities
├── supabase/
│   └── migrations/        # SQL migration files
├── data/                  # Album data (CSV, images)
├── docs/                  # Architecture documentation
├── plans/                 # Design and planning docs
├── scripts/               # Utility/automation scripts
└── .github/               # CI/CD workflows
```

## Tech Stack

- **Frontend:** Next.js 16 (App Router) + React 19 + TypeScript
- **Backend:** Python 3.13+
- **Database:** PostgreSQL via Supabase
- **UI Components:** shadcn/ui + Tailwind CSS v4
- **Package Manager:** npm (lockfile v3)
- **Monorepo:** npm workspaces

## Database Schema

Three core tables in PostgreSQL (see `supabase/migrations/`):

- **users** - user accounts with email, password hash, subscription status, email verification
- **albums** - jazz album catalog with title, artist, release year, cover image, streaming links
- **recommendations** - join table linking users to recommended albums with sent date

All primary keys are UUIDs (via `uuid-ossp` extension). Foreign keys use `ON DELETE CASCADE`. Timestamps use `TIMESTAMP WITH TIME ZONE`.

## Development Setup

### Prerequisites

- Node.js 18+
- npm
- Python 3.13+ (for backend scripts)
- Supabase CLI

### Supabase

```bash
npm install supabase --save-dev
npx supabase login
npx supabase link --project-ref [your-project-ref]
```

The project-ref is found in your Supabase project URL: `https://app.supabase.com/project/[project-ref]`.

## Conventions

### Code Organization

- Frontend uses Next.js App Router (`src/app/` for pages and API routes)
- UI components in `src/components/` (shadcn/ui primitives in `src/components/ui/`)
- Supabase client setup in `src/lib/supabase/` (browser, server, and middleware clients)
- Backend Python scripts in `packages/backend/src/`
- Database changes go through migrations in `supabase/migrations/`

### Database

- Use UUIDs for all primary keys
- Table names are lowercase, plural (e.g., `users`, `albums`)
- All timestamp columns use `TIMESTAMP WITH TIME ZONE`
- Foreign keys must include `ON DELETE CASCADE`

### Git Workflow

- Feature branches with pull requests
- Descriptive commit messages (e.g., "Add is_email_verified field to users table")

## Current Project Status

**Implemented:**
- User authentication (Supabase Auth with email/password)
- User registration with email confirmation
- Newsletter frequency preferences (daily/weekly/monthly)
- Album database schema and seeding from CSV
- OCR-based album data extraction (Python)
- Protected routes with auth middleware
- Navigation based on auth state

**Not yet implemented:**
- Email scheduling/sending logic
- Recommendation algorithm
- Album cover images and streaming links
- Tests
- CI/CD workflows

## Key Files

| File | Purpose |
|------|---------|
| `package.json` | Root monorepo config, Supabase dev dependency |
| `supabase/migrations/` | Database schema migrations |
| `packages/frontend/src/lib/supabase/` | Supabase client setup (browser, server, middleware) |
| `packages/frontend/src/app/` | Next.js pages and API routes |
| `packages/backend/src/main.py` | Album seeding script |
| `data/albums.csv` | Album catalog data |
| `docs/folder-structure.md` | Architecture rationale and structure proposal |
| `plans/database_schema.md` | Database design documentation with ER diagram |
