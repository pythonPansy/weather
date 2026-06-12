---
name: ce-compound
description: >-
  Captures solved problems into docs/solutions/ and proposes updates to Cursor
  rules or skills so the same mistake is caught next time. Use after a fix is
  verified, when debugging is done, or when the user says compound, ce-compound,
  or document this learning. Does not edit rules without human approval.
disable-model-invocation: true
---

# ce-compound — teach the system

Turn a solved problem into reusable knowledge. **Read-only on rules** until the user approves updates.

## Allowed without extra approval

- Read codebase and conversation context
- Write `docs/solutions/YYYY-MM-DD-<slug>.md` from `docs/solutions/_template.md`
- Update the related plan's status if appropriate

## Requires explicit approval

- Edits to `.cursor/rules/`, `.cursor/skills/`, `docs/*.md` (except new solution files)
- New CI checks or hooks

## Workflow

1. **Extract** — Problem, root cause, fix (paths), verification steps.
2. **Classify** — Tag category: `conventions`, `testing`, `ingestion`, `config`, etc.
3. **Write solution** — `docs/solutions/YYYY-MM-DD-<slug>.md` with YAML frontmatter (`symptoms`, `prevention`).
4. **Propose system updates** — Bullet list, e.g.:
   - Add one paragraph to `compound_engineering.mdc` or a scoped rule
   - Extend a skill with a "known pitfall"
   - Add a test or lint guard
5. **STOP** — Ask:

   > Solution saved to `docs/solutions/...`. Apply the proposed rule/skill updates? Reply **yes** to apply, or edit the proposal.

Apply rule/skill edits only after **yes** / **apply** / **approved**.

## Quality bar

- Searchable symptoms (error messages, file names).
- Prevention must be actionable for the next agent session.
- Link to plan/PR if available.

## Verify compounding

Ask: *Would the next agent catch this automatically?* If not, strengthen the proposed rule or test.
