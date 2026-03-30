---
name: git-commit
description: Create Git commits safely and consistently. Use when reviewing staged changes, choosing commit scope/type, writing commit messages, or executing commits with commit hygiene rules.
metadata: {"clawdbot":{"emoji":"📝","requires":{"bins":["git"]}}}
---

# Git Commit

Create clean, reviewable commits from actual staged changes.

## Use this skill for

- checking what is staged before commit
- grouping changes into a commit
- writing a good commit message
- executing `git commit`
- deciding whether to use `feat`, `fix`, `docs`, `chore`, etc.

Do **not** use this skill for broad branch/rebase/remote workflows unless they directly affect the commit you are making.

## Commit workflow

### 1. Inspect first

Always inspect status and staged diff before committing.

```bash
git status --short
git diff --staged
```

If nothing is staged, inspect working tree changes:

```bash
git diff
```

### 2. Stage intentionally

Prefer targeted staging over blanket staging.

```bash
git add path/to/file
git add path/to/file1 path/to/file2
git add -p
```

Avoid `git add .` unless you have already verified the worktree is clean and all changed files belong in the commit.

### 3. Choose the commit type

Use conventional commit style when possible:

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation only
- `refactor`: code restructure without feature/bug behavior change
- `test`: tests added or changed
- `chore`: maintenance or housekeeping
- `ci`: CI/config automation changes
- `build`: build or dependency changes
- `perf`: performance improvement
- `revert`: reverting prior commit

Format:

```text
<type>[optional scope]: <short description>
```

Examples:

```text
fix(auth): handle expired token refresh
feat(profile): add avatar upload flow
docs(readme): clarify local setup
chore(skills): add git-commit skill scaffold
```

### 4. Write the message from the diff

The message should describe the actual change, not vague intent.

Good:
- `fix(mail): route agentmail hooks through local handler`
- `docs(skills): add commit workflow guidance`

Bad:
- `update stuff`
- `fix issues`
- `changes`

Rules:
- imperative mood: `add`, `fix`, `remove`
- keep subject concise
- one logical change per commit
- if the change needs explanation, add a body

### 5. Commit

Single-line commit:

```bash
git commit -m "<type>[scope]: <description>"
```

With body:

```bash
git commit -m "<type>[scope]: <description>" -m "Why this change was needed and any important implementation detail."
```

## Shortcut-linked commit naming

When work is tied to a Shortcut story, prefer including the story reference in the commit subject where applicable.

Format:

```text
Some ticket name [sc-####]
```

Examples:

```text
fix(auth): handle refresh token expiry [sc-1234]
feat(profile): add avatar cropping flow [sc-4821]
```

Use this when:
- the work clearly maps to a Shortcut story
- the story id is known
- adding the reference keeps the subject readable

Do not force it when there is no relevant Shortcut ticket.

## Safety rules

- never commit secrets, tokens, `.env` files, or private keys
- never mix unrelated changes in one commit
- do not use `--no-verify` unless explicitly asked
- do not amend or rewrite commits unless explicitly asked
- if hooks fail, read the failure and fix the issue before retrying
- if the worktree contains unrelated edits, call that out before committing

## Recommended decision pattern

Before committing, answer briefly:
1. What files are staged?
2. Is this one logical change?
3. What is the correct commit type?
4. What short message best matches the diff?

Then commit only after those answers are clear.
