# Project Refactoring Plan

This plan outlines the steps to refactor the project structure to follow best practices.

## 1. Remove redundant `src` folder

- [ ] List the content of `packages/frontend/src`.
- [ ] Move the content of `packages/frontend/src/components` to `packages/frontend/components`.
- [ ] Remove the `packages/frontend/src` directory.
- [ ] Update any import paths in the frontend code.

## 2. Consolidate database schemas

- [ ] Read the content of `packages/database/schema.sql`.
- [ ] Create a new migration file in `supabase/migrations` with the content of `packages/database/schema.sql`.
- [ ] Delete `packages/database/schema.sql`.

## 3. Organize data files

- [ ] List the content of `data` and `packages/database/seeds`.
- [ ] Move all files from `packages/database/seeds` to `data`.
- [ ] Remove the `packages/database/seeds` directory.

## 4. Configure monorepo

- [ ] Read the root `package.json`.
- [ ] Add the `packages/frontend` workspace to the `package.json`.
- [ ] Run `npm install` to update the monorepo.

