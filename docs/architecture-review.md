# Architecture Review

**Date:** 2026-03-25
**Scope:** Full codebase review (frontend, backend, database, CI/CD, infrastructure)

---

## Summary

Jazzy is a well-structured monorepo for a jazz album recommendation newsletter service. The architecture demonstrates strong separation of concerns, idempotent data pipelines, and thoughtful fallback strategies. Below is a detailed review with findings organized by severity.

---

## Architecture Overview

```
User ──► Next.js 16 (Vercel) ──► Supabase Auth + PostgreSQL
                                        ▲
GitHub Actions (04:00 UTC daily) ───────┘
  └─► send_recommendations.py ──► Resend API ──► User inbox

GitHub Actions (manual trigger)
  └─► main.py orchestrator
        ├─► extract_album_data.py (Gemini 2.0 Flash vision)
        ├─► add_streaming_links.py (Spotify + iTunes + UPC bridge)
        └─► parallel: add_album_covers.py + add_album_summaries.py (Perplexity)
```

**Tech Stack:** Next.js 16 / React 19 / TypeScript 6 / Tailwind v4 / shadcn/ui / Python 3.13 (uv) / Supabase / Resend / GitHub Actions

---

## Strengths

### 1. Idempotent Data Pipeline
Each backend script checks database state before processing, skipping already-complete records. This makes the seeding pipeline safe to re-run without duplicating work or corrupting data.

### 2. Multi-Strategy Streaming Link Resolution
The `add_streaming_links.py` script implements a sophisticated fallback chain: exact match → ASCII normalization → stripped parentheticals → artist fallback, plus a UPC barcode bridge between Spotify and Apple Music for high-confidence cross-platform matching.

### 3. Metadata Preservation on Substitution
When an Apple Music substitute album is used, original metadata (`original_title`, `original_artist`, `original_release_year`) is preserved in dedicated columns, maintaining data lineage.

### 4. Pipeline Dependency Ordering
Streaming links run before covers and summaries because substitutions modify album metadata. Covers and summaries then run in parallel since they're independent. This is correctly modeled in `main.py`.

### 5. Clean Auth Architecture
Three-client Supabase setup (browser, server, middleware) follows best practices. Middleware-based route protection is centralized and consistent. RLS policies enforce data isolation at the database level.

### 6. Claude Agent SDK for Verification
Using an LLM agent to verify album record accuracy (factual correctness, URL validity, summary coherence) is an innovative QA approach that catches errors a heuristic check would miss.

### 7. Graceful Degradation
Missing optional APIs (Spotify credentials absent, Perplexity down) produce warnings but don't crash the pipeline. Each script handles its own rate limiting with exponential backoff.

---

## Findings

### Critical

*None identified.* The architecture is sound for the current scale and use case.

### High Priority

#### H1. No Test Coverage
**Location:** Entire codebase
**Impact:** Regressions go undetected; refactoring is risky

The project has no meaningful test suite. The only test file (`test_extract_album_data.py`) depends on a local Ollama instance and is outdated (the script now uses Gemini). Key untested areas:

- Recommendation selection algorithm (calendar ordering, wraparound, frequency logic)
- Email template rendering (conditional sections, streaming links, substitution labels)
- Streaming link normalization and fuzzy matching
- Unsubscribe/account deletion RPC functions
- Auth middleware redirect logic

**Recommendation:** Prioritize unit tests for the recommendation selection algorithm and email template rendering, as these are the most business-critical paths with the most conditional logic.

#### H2. Supabase Browser Client Recreated on Every Render
**Location:** `packages/frontend/src/lib/supabase/client.ts` (called in every client component)
**Impact:** Unnecessary object allocation; potential auth state inconsistency

Each component calls `createClient()` independently, creating a new Supabase client instance on every render. While `@supabase/ssr` may deduplicate internally, this pattern is fragile.

**Recommendation:** Wrap the browser client in a React context provider or a module-level singleton to ensure a single instance is shared across components.

#### H3. Admin Client Created Inline in Route Handler
**Location:** `packages/frontend/src/app/auth/confirm/route.ts`
**Impact:** Service role key handling scattered; harder to audit

The Supabase admin client (using the service role key) is instantiated inline in the auth confirmation route handler rather than through a shared utility.

**Recommendation:** Extract admin client creation to `src/lib/supabase/admin.ts` for centralized secret handling and reuse.

### Medium Priority

#### M1. Database Connection Staleness in Long-Running Scripts
**Location:** `packages/backend/src/scripts/extract_album_data.py`, `add_streaming_links.py`
**Impact:** Potential connection timeouts during image processing

Long-running scripts (especially vision extraction) may exceed Supabase connection idle timeouts. The explicit reconnection after parallel phases in `extract_album_data.py` mitigates this but isn't systematic.

**Recommendation:** Implement a connection health check or lazy reconnection wrapper for the Supabase client used in backend scripts.

#### M2. No Environment Variable Validation in Frontend
**Location:** `packages/frontend/next.config.ts`
**Impact:** Cryptic runtime errors if env vars are missing

The Next.js config doesn't validate required environment variables at build time. Missing `NEXT_PUBLIC_SUPABASE_URL` or `SUPABASE_SERVICE_ROLE_KEY` would produce confusing errors.

**Recommendation:** Add a validation block in `next.config.ts` or a startup check using `zod` to fail fast with clear error messages.

#### M3. Unused Navigation Component
**Location:** `packages/frontend/src/components/navigation.tsx`
**Impact:** Dead code; confusing for contributors

The `Navigation` component implements auth-aware navigation (settings link for authenticated users, login/register for guests) but is never imported in the layout or any page.

**Recommendation:** Either integrate it into `layout.tsx` or remove it to avoid confusion.

#### M4. Recommendation History Full Reset
**Location:** `packages/backend/src/send_recommendations.py`
**Impact:** Users receive duplicate recommendations without indication

When all albums have been sent to a user, the entire recommendation history is deleted and the cycle restarts from the beginning. Users have no way to know they're receiving a repeat.

**Recommendation:** Consider adding a "cycle" counter or a visual indicator in the email (e.g., "From the archives" label) when re-sending previously recommended albums.

#### M5. Thread-Shared Rate Limit Flag
**Location:** `packages/backend/src/scripts/add_streaming_links.py`
**Impact:** Potential race condition under concurrent access

The global `_spotify_rate_limited` flag is read and written across threads without synchronization. While current concurrency is limited (MAX_WORKERS=1), this would break if parallelism is increased.

**Recommendation:** Use `threading.Event()` or `threading.Lock()` if concurrency is ever increased.

### Low Priority

#### L1. Missing Error Boundaries in Frontend
**Location:** `packages/frontend/src/app/`
**Impact:** Unhandled component errors show a blank page

No React error boundaries are defined. A runtime error in any component (e.g., failed Supabase call during render) would crash the entire page with no recovery UI.

**Recommendation:** Add a root `error.tsx` boundary and per-route error boundaries for graceful degradation.

#### L2. No Security Headers Configuration
**Location:** `packages/frontend/next.config.ts`
**Impact:** Missing defense-in-depth headers

No custom security headers (CSP, X-Frame-Options, X-Content-Type-Options, etc.) are configured in the Next.js config or Vercel settings.

**Recommendation:** Add security headers in `next.config.ts` using the `headers()` function.

#### L3. Loading States Could Be Improved
**Location:** `packages/frontend/src/app/settings/page.tsx`
**Impact:** Brief flash of empty content on page load

The settings page shows empty/default state while user data and frequency preferences are loading. No loading skeleton or spinner is displayed.

**Recommendation:** Add a `loading.tsx` file or use Suspense boundaries with skeleton UI.

#### L4. Inconsistent Text Normalization
**Location:** `packages/backend/src/scripts/add_streaming_links.py`
**Impact:** Edge-case mismatches in fuzzy album search

Diacritic stripping and text normalization differ between `_to_search_query()` and `_normalize()` functions in the streaming link lookup script. This could cause missed matches for albums with special characters.

**Recommendation:** Consolidate normalization logic into a single shared utility function.

#### L5. No `original_release_year` Column
**Location:** `supabase/migrations/20260323120000_add_original_album_columns.sql`
**Impact:** Original release year lost on Apple Music substitution

The migration adds `original_title` and `original_artist` but not `original_release_year`, even though `release_year` is overwritten during Apple Music substitution. The CLAUDE.md mentions this column exists, but it doesn't.

**Recommendation:** Add `original_release_year` column to preserve this data, or update documentation to reflect the actual schema.

---

## Database Schema Assessment

The schema is clean and appropriate for the current scale:

- **3 tables** with clear relationships (users → recommendations ← albums)
- **UUIDs** for all primary keys (good for distributed systems, Supabase compatibility)
- **RLS policies** enforce row-level isolation correctly
- **Cascading deletes** prevent orphaned records
- **Auto-trigger** on `auth.users` INSERT keeps public.users in sync

**One concern:** The `calendar_order` UNIQUE constraint on albums means only one album per day-of-year. If the catalog expands beyond 366 albums, this constraint will need rethinking.

---

## CI/CD Assessment

Four GitHub Actions workflows provide good coverage:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `send-recommendations.yml` | Daily cron (04:00 UTC) + manual | Email distribution |
| `seed-database.yml` | Manual only | Album data pipeline |
| `claude-code-review.yml` | PR events | Automated code review |
| `claude.yml` | Issue/PR comments with @claude | Interactive AI assistance |

**Missing:** No build/lint/test CI for the frontend. PRs can merge without verifying the Next.js build succeeds or linting passes.

**Recommendation:** Add a workflow that runs `npm run build` and `npm run lint` on PRs touching `packages/frontend/`.

---

## Architectural Recommendations Summary

| Priority | Finding | Effort |
|----------|---------|--------|
| High | Add test coverage for core business logic | Large |
| High | Singleton Supabase browser client | Small |
| High | Extract admin client to shared utility | Small |
| Medium | Add frontend env var validation | Small |
| Medium | Remove or integrate unused Navigation component | Small |
| Medium | Add frontend build/lint CI workflow | Medium |
| Medium | Improve recommendation cycle UX | Medium |
| Low | Add error boundaries | Small |
| Low | Add security headers | Small |
| Low | Add loading states/skeletons | Small |
| Low | Add `original_release_year` column | Small |
