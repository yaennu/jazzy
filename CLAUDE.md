# CLAUDE.md

## Project Overview

Jazzy is a web application where users subscribe to receive periodic jazz album recommendations via email. It is a monorepo built with Node.js/TypeScript, using Supabase (PostgreSQL) as the database backend.

**License:** GPLv3

## Repository Structure

```
jazzy/
├── packages/
│   ├── frontend/          # React/TypeScript frontend
│   │   ├── public/        # Static assets
│   │   ├── src/
│   │   │   ├── components/    # Reusable UI components
│   │   │   ├── pages/         # Page-level views
│   │   │   └── services/      # API integration & utilities
│   │   └── tests/
│   ├── backend/           # Node.js/TypeScript backend service
│   │   ├── src/
│   │   ├── config/        # Environment configurations
│   │   └── tests/
│   └── database/          # Supabase/PostgreSQL
│       ├── migrations/    # SQL migration files
│       ├── seeds/         # Data seeding scripts
│       └── schema.sql     # Current database schema
├── docs/                  # Architecture documentation
├── plans/                 # Design and planning docs
├── scripts/               # Utility/automation scripts
└── .github/               # CI/CD workflows
```

## Tech Stack

- **Frontend:** React + TypeScript
- **Backend:** Node.js + TypeScript
- **Database:** PostgreSQL via Supabase
- **Package Manager:** npm (lockfile v3)
- **Monorepo:** npm workspaces

## Database Schema

Three core tables in PostgreSQL (see `packages/database/schema.sql`):

- **users** - user accounts with email, password hash, subscription status, email verification
- **albums** - jazz album catalog with title, artist, release year, cover image, streaming links
- **recommendations** - join table linking users to recommended albums with sent date

All primary keys are UUIDs (via `uuid-ossp` extension). Foreign keys use `ON DELETE CASCADE`. Timestamps use `TIMESTAMP WITH TIME ZONE`.

## Development Setup

### Prerequisites

- Node.js 18+
- npm
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

- Frontend follows `components/`, `pages/`, `services/` pattern
- Backend separates source (`src/`) and config (`config/`)
- Database changes go through migrations in `packages/database/migrations/`

### Database

- Use UUIDs for all primary keys
- Table names are lowercase, plural (e.g., `users`, `albums`)
- All timestamp columns use `TIMESTAMP WITH TIME ZONE`
- Foreign keys must include `ON DELETE CASCADE`

### Git Workflow

- Feature branches with pull requests
- Descriptive commit messages (e.g., "Add is_email_verified field to users table")

## Current Project Status

The project has its architecture and database schema defined. Frontend source, backend source, tests, CI/CD pipelines, and migration scripts are not yet implemented. The `src/` and `tests/` directories in both frontend and backend packages are placeholders awaiting development.

## Key Files

| File | Purpose |
|------|---------|
| `package.json` | Root monorepo config, Supabase dev dependency |
| `packages/database/schema.sql` | Canonical database schema |
| `docs/folder-structure.md` | Architecture rationale and structure proposal |
| `plans/database_schema.md` | Database design documentation with ER diagram |
| `.kilocode/mcp.example.json` | GitHub MCP server config template |
