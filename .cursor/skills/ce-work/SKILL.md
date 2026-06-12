---
name: ce-work
description: >-
  Implements an approved plan in the weather pipeline after explicit human
  approval. Creates a feature branch, executes docs/plans/ steps, runs local
  validation. Use only after ce-plan and user approval (approved, proceed,
  LGTM). Never use for planning or for work without an approved plan unless
  user said skip plan.
disable-model-invocation: true
---

# ce-work — implement after approval

**Gate:** Do not start until ALL are true:

1. A plan exists at `docs/plans/*.md` with implementation steps.
2. The user **explicitly approved** in this conversation (*approved*, *proceed*, *implement the plan*, *LGTM*).
3. Plan approval section is updated to **approved** with date (edit the plan file).

If any gate fails → run `ce-plan` or ask the user to approve. **Do not create a branch or edit code.**

## Opt-out

User may say **skip plan** for trivial one-file fixes. Confirm scope in one sentence, then implement without a plan doc.

## Workflow

### 1. Confirm gates

Quote the plan path and approval phrase. If missing, stop.

### 2. Branch (first mutating git step)

```bash
rtk git status
git checkout main   # or branch user specified
git pull               # if user approves network
git checkout -b feature/<slug-from-plan>
```

Ask before `git pull` if unsure. Never force-push.

### 3. Execute plan

- Follow steps in order; tick progress in chat.
- Match repo conventions (`cursor_instructions.mdc`, scoped rules).
- Minimal diff — no drive-by refactors.

### 4. Validate locally (safe commands)

```bash
rtk uv run ruff check ./src ./tests
rtk uv run pytest <paths from plan> -q
```

Fix failures before finishing.

### 5. Hand off

Summarize: branch name, files changed, validation run, remaining manual steps (deploy, target-env checks).

- Do **not** commit unless the user asks.
- Do **not** deploy or query target environments without approval.

## During work

- If the plan is wrong, **stop** and propose a plan revision — do not silently diverge.
- If scope grows, ask whether to extend the plan.

## After implementation

Suggest `ce-compound` if the work surfaced reusable learnings.
