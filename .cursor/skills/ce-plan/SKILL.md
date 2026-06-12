---
name: ce-plan
description: >-
  Research-only implementation planning for the weather pipeline. Writes
  docs/plans/ from codebase and docs review. Use when starting a feature, fix,
  or refactor; before any branch or code changes; when the user says plan,
  ce-plan, or compound plan. Stops for human approval before implementation.
disable-model-invocation: true
---

# ce-plan — plan before code

**Read-only phase.** Do not create branches, commit, or edit implementation files.

## Allowed

- Read, Grep, Glob, semantic search
- Write **only** under `docs/brainstorms/` or `docs/plans/`
- `rtk git log`, `rtk git diff`, `rtk git status` (read-only)
- Local validation commands that do not touch target environments

## Forbidden until user approves plan

- `git checkout -b`, worktrees, commits
- Edits to `src/`, `tests/`, `pyproject.toml`, etc.
- Target-environment commands (see `.cursor/rules/shell_and_environment.mdc`)

## Workflow

1. **Clarify** — If requirements are ambiguous, ask up to 3 focused questions; then continue with stated assumptions.
2. **Research** — Read `docs/ai_assisted_development.md`, `.cursor/rules/cursor_instructions.mdc`, and similar code under `src/tasks/`.
3. **Write plan** — Copy `docs/plans/_template.md` to `docs/plans/YYYY-MM-DD-<short-slug>.md`. Fill all sections; set `status: draft` and approval checkbox **waiting**.
4. **Present summary** — Short bullet summary in chat: scope, files, validation, risks.
5. **STOP** — End with:

   > Plan written to `docs/plans/...`. Review and reply **approved** (or **proceed** / **implement the plan**) to start `ce-work`. I will not create a branch or edit code until then.

Do not implement. Do not create a branch.

## Plan quality bar

- Name concrete files and modules (`BaseTask`, `register_task`, `TaskRunner`, task YAML).
- Include validation commands from `cursor_instructions.mdc` (`rtk uv run ruff`, `rtk uv run pytest`).
- State what is out of scope.

## Optional brainstorm

If requirements are fuzzy, write `docs/brainstorms/YYYY-MM-DD-<slug>.md` first, get alignment, then plan.
