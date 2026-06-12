# AI-assisted development

Human-in-the-loop workflow for agent-assisted development. Full rule: `.cursor/rules/compound_engineering.mdc`.

## Skills (project)

| Skill | When | Human gate |
| ----- | ---- | ---------- |
| **ce-plan** | New feature, fix, refactor | Approve written plan before any code |
| **ce-work** | After plan approved | Approve branch/deploy/commit as needed |
| **ce-compound** | After verified fix | Approve rule/skill updates |

Invoke in Agent chat, e.g. *use ce-plan to add CSV export* or *run ce-work* after approving a plan.

## Artifacts

```
docs/brainstorms/   # optional requirements (_template.md)
docs/plans/         # required before ce-work (_template.md)
docs/solutions/     # learnings after fixes (_template.md)
```

## Typical session

1. **You:** Describe the task → ask for **ce-plan**
2. **Agent:** Researches, writes `docs/plans/YYYY-MM-DD-….md`, stops
3. **You:** Review plan → reply **approved**
4. **Agent:** **ce-work** — creates branch, implements, runs local validation
5. **You:** Review diff, test (live API calls need approval)
6. **Agent:** **ce-compound** — documents solution; proposes rule updates
7. **You:** Approve rule changes if useful

## RTK — token-efficient shell commands

[RTK](https://www.rtk-ai.app/) (Rust Token Killer) compresses verbose command output before it reaches the agent context (~60–90% savings on pytest, git, ruff).

### Install (do not use `pip install rtk`)

That installs a **different** package. Install [rtk-ai](https://www.rtk-ai.app/docs/getting-started/installation/) instead:

- Windows: download zip, add `rtk.exe` to PATH
- Or: `cargo install --git https://github.com/rtk-ai/rtk rtk`

Verify: `rtk --version` and `rtk gain`.

### Global Cursor hook (transparent rewrite)

```bash
rtk init --global --agent cursor
```

Restart Cursor. The hook rewrites agent Shell commands (e.g. `uv run pytest` → filtered output) via `preToolUse` in `~/.cursor/hooks.json`. This is **global**, not checked into this repo.

### Project rules (fallback)

`.cursor/rules/shell_and_environment.mdc` tells agents to use `rtk uv run …` and `rtk git …` when the global hook is absent.

| Context | Command |
| ------- | ------- |
| Agent tests | `rtk uv run pytest <path> -q` |
| Agent lint | `rtk uv run ruff check ./src ./tests` |
| Agent git | `rtk git diff -- <paths>` |

Override one command: `RTK_DISABLED=1 uv run pytest …`

### Windows vs WSL

| Environment | RTK auto-rewrite |
| ----------- | ---------------- |
| Native Windows | No — use explicit `rtk uv run …` per project rules |
| WSL (Cursor opened on WSL workspace) | Yes — hooks work like Linux |

**WSL setup:**

1. Clone/open repo in WSL (e.g. `~/source/repos/weather`)
2. Install uv + rtk-ai in WSL; verify `rtk gain`
3. `rtk init --global --agent cursor` in WSL; restart Cursor on the WSL folder
4. `uv sync --extra dev`

Pick one primary environment — mixing Windows and WSL on the same clone causes duplicate venvs.

### RTK vs project ruff hooks

These are complementary:

| Hook | Location | Event | Purpose |
| ---- | -------- | ----- | ------- |
| RTK | Global `~/.cursor/hooks.json` | `preToolUse` | Filter agent shell output |
| Ruff | Project `.cursor/hooks.json` | `afterFileEdit`, `stop` | Auto-lint edited `.py` files |

Ruff hooks use plain `uv run ruff` internally (not RTK).

## Project hooks — auto ruff after agent edits

Pre-commit runs ruff on commit; hooks run **during** agent sessions.

### One-time setup

Hooks are already in `.cursor/hooks.json`. Restart Cursor and check **Settings → Hooks** for `afterFileEdit` and `stop`.

| Hook | When | Action |
| ---- | ---- | ------ |
| `afterFileEdit` | Agent edits `.py` under `src/`, `tests/` | `ruff check --fix` + `ruff format` on that file |
| `stop` | Agent finishes a turn | ruff on changed `.py` files in git diff |

Requires `uv` on PATH.

## Related docs

- Agent rules: `.cursor/rules/cursor_instructions.mdc`
- Learning roadmap: `NextSteps.md`
