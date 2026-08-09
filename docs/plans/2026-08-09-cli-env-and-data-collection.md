---
status: approved
created: 2026-08-09
approval: approved
---

# Plan: CLI, env expansion, and first data collection

## Goal

Make the existing YAML pipeline runnable from the command line so weather and tides data can be collected into gitignored Parquet files under `data/`, with `${ENV_VAR}` placeholders in config expanded from the environment. Document a minimal local/cron loop for ongoing collection — no heavy orchestration framework.

## Background

- `config/pipeline.yaml` already chains `weather_api` → `weather_parquet` → `tides_api` → `tides_parquet`.
- Export tasks append one row per run (`fetched_at` + JSON `response`).
- `TaskRunner` loads YAML but there is no `__main__` / CLI entrypoint.
- Config uses `api_key: ${OPENWEATHER_API_KEY}`, but the runner does **not** expand env placeholders today (literal string would be sent to the API).
- `data/` is gitignored; README already describes the intended layout.

## Scope

### In scope

- Env-var expansion for string params in loaded YAML (at least `${VAR}` → `os.environ["VAR"]`, with a clear error if missing)
- Thin CLI: `uv run python -m src config/pipeline.yaml` (or equivalent) that constructs `TaskRunner`, runs it, exits non-zero on failure
- Unit tests for expansion and CLI argument handling (mocked tasks / no live APIs)
- README notes: set `OPENWEATHER_API_KEY`, one-shot run, optional cron example
- Keep using existing `config/pipeline.yaml` and Parquet append behaviour

### Out of scope

- Airflow, Prefect, Kubernetes, cloud schedulers, cron/systemd examples (user: CLI only, no orchestration)
- Custom exception hierarchy (separate `NextSteps.md` item; may land before or after)
- Task dependencies graph, incremental/skip-if-fresh runs
- Multi-site config generation, secrets managers, Docker packaging
- Changing API providers or Parquet schemas
- Committing collected data
- Manual live smoke against real APIs (needs separate approval)

## Design

### Env expansion

Small helper (e.g. `src/config_env.py` or method on `TaskRunner`):

- Walk task `params` (and nested dict/list values if present)
- Replace strings matching `^\$\{([A-Za-z_][A-Za-z0-9_]*)\}$` (whole-string placeholder) with `os.environ[name]`
- Raise a clear error if the variable is unset/empty
- Do not expand mid-string interpolations in this pass (keeps behaviour simple and testable)

### CLI

```text
uv run python -m src <config_path>
```

- `src/__main__.py`: parse argv (stdlib `argparse`), call `TaskRunner(path).run()`, log start/finish
- Exit code `0` on success; non-zero on missing config, missing env, HTTP/task errors
- No new third-party CLI framework

### Collection loop (ops, not code)

After implementation, operator workflow:

1. `export OPENWEATHER_API_KEY=…`
2. `uv run python -m src config/pipeline.yaml` — verify `data/weather.parquet` and `data/tides.parquet`
3. Schedule the same command (cron / Task Scheduler / systemd timer), e.g. hourly

Tides currently need no API key; weather requires OpenWeatherMap.

## Files to touch

| File | Change |
| ---- | ------ |
| `src/config_env.py` (or similar) | Expand `${VAR}` in config structures |
| `src/runner.py` | Apply expansion after YAML load (before tasks run) |
| `src/__main__.py` | CLI entrypoint |
| `tests/test_config_env.py` | Expansion success/failure cases |
| `tests/test_main.py` (or `tests/test_cli.py`) | CLI parses path, invokes runner (mocked) |
| `README.md` | Run + env + cron notes |
| `config/pipeline.yaml` | Only if needed for clarity (paths/comments); behaviour otherwise unchanged |
| `NextSteps.md` | Mark CLI done when implemented (optional) |

## Implementation steps

1. **TDD — env expansion** — tests for replace, missing var, non-string passthrough, nested values if supported.
2. **Implement expansion** and wire into `TaskRunner` after `yaml.safe_load`.
3. **TDD — CLI** — mock `TaskRunner.run`; assert exit codes / argv.
4. **Implement `src/__main__.py`** with `argparse`.
5. **Update README** with export key, one-shot command, cron example, reminder not to commit `data/` or secrets.
6. **Validate** unit tests + ruff (no live API in default pytest).
7. **Manual live smoke** (requires user approval for live APIs): set key, run once against `config/pipeline.yaml`, confirm Parquet row counts.

## Validation

```bash
rtk uv run ruff check ./src ./tests
rtk uv run ruff format --check .
rtk uv run pytest tests/test_config_env.py tests/test_main.py -q
rtk uv run pytest -q
```

Live (opt-in, needs approval + `OPENWEATHER_API_KEY`):

```bash
export OPENWEATHER_API_KEY=…
uv run python -m src config/pipeline.yaml
# inspect data/weather.parquet and data/tides.parquet
```

## Risks

- Whole-string-only `${VAR}` expansion may surprise if someone writes `prefix-${VAR}`; document the rule.
- Single shared `PipelineContext` for weather then tides in one YAML is fine today; a failure mid-pipeline may leave weather written and tides not — acceptable for v1; note in README.
- Cron working directory must be the repo root (or use absolute config/output paths) or relative `data/` paths will land elsewhere.

## Approval

- [ ] **waiting** — stored for later; user has not approved implementation
- [x] **approved** — date: 2026-08-09 (user: implement outstanding plans; CLI only, no orchestration)
