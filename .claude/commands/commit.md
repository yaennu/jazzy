---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git diff:*), Bash(git push:*), Bash(gh:*)
description: Group changed files by theme, create conventional commits, and open a PR via gh
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits (for style reference): !`git log --oneline -10`

## Your task

Based on the above changes, create thematic commits.

### Step 1 — Analyze & group

Examine all changed, staged, and untracked files. Group them into thematic clusters based on what they change (e.g. "documentation", "test fixes", "logging refactor", "new feature X"). Each group should be a logically cohesive unit of work.

If all changes belong to a single theme, a single commit is perfectly fine. Only split into multiple commits when the changes are clearly distinct.

### Step 2 — Propose commit plan

Present the grouping as a numbered list. For each group show:

1. **Commit message** (Conventional Commits format)
2. **Files** included in that commit

Commit messages MUST follow **Conventional Commits**:

```
type(scope): description
```

- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`, `build`
- **Scope**: optional but encouraged (e.g. `fix(tests): patch is_mock_mode`)
- **Description**: lowercase, imperative mood, no trailing period

### Step 3 — Wait for approval

Do NOT execute any commits yet. Wait for the user to approve, adjust groupings, or edit commit messages.

### Step 4 — Execute

Once approved, execute the commits sequentially. For each group:
1. Stage only the files belonging to that group (`git add <file1> <file2> ...`)
2. Create the commit with the approved message

### Step 5 — Push & open PR

After all commits are created:
1. Push the current branch to the remote (`git push -u origin <branch>`)
2. Create a pull request using `gh pr create` with:
   - A title summarizing the overall change
   - A body listing the commits made
   - Target the `dev` branch

If a PR already exists for the branch, skip PR creation and just push.
