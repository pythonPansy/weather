---
status: completed
created: 2026-08-09
approval: approved
completed: 2026-08-09
---

# Plan: Typed pipeline context wrapper

## Implementation status

**Completed** — merged on `main` (PR #2). `PipelineContext` in `src/context.py`; all ingest/export
tasks and tests migrated.

## Goal

Replace the bare `dict` shared across tasks with a typed `PipelineContext` wrapper in `src/context.py`, so ingest and export tasks share a clear, typed contract for known keys (`weather`, `weather_call`, `tides`, `tides_call`, parquet paths) while keeping nested API payloads as `dict` for now.

## Scope

### In scope

- Implement `PipelineContext` in the empty `src/context.py`
- Update `BaseTask.run` signature from `dict` to `PipelineContext` (also fix the misnamed `config` parameter)
- Migrate `TaskRunner` and all ingest/export tasks to create/read/write `PipelineContext`
- Add unit tests for the wrapper; update existing task tests to use it
- Prefer returning an updated context from `run` (immutable-where-practical via `dataclasses.replace` or equivalent copy-on-write setters)

### Out of scope

- Custom exception hierarchy (next `NextSteps.md` item; keep clear `KeyError` / helper messages for now)
- Fully typing nested OpenWeatherMap / TideTurtle payload shapes
- CSV export, CLI, task dependencies, incremental runs, mypy/ty CI wiring
- Live API behaviour changes

## Design

```python
@dataclass(frozen=True)
class PipelineContext:
    weather: dict | None = None
    weather_call: dict | None = None
    tides: dict | None = None
    tides_call: dict | None = None
    parquet_path: str | None = None
    tides_parquet_path: str | None = None

    def require(self, field: str) -> object:
        """Return a required field or raise KeyError with a task-oriented message."""
        ...

    def with_values(self, **kwargs) -> PipelineContext:
        """Return a new context with the given fields replaced."""
        ...
```

Notes:

- Frozen dataclass + `with_values` matches the existing “return updated context” pattern without silent shared mutation.
- Nested vendor JSON stays `dict` until a later typing pass.
- Export tasks use `context.require("weather")` (etc.) instead of ad-hoc `"x" not in context` checks.
- No dict-subscript API on the wrapper — migrate call sites to attributes/`require` so tests exercise the real contract.

## Files to touch

| File | Change |
| ---- | ------ |
| `src/context.py` | Add `PipelineContext` |
| `src/tasks/base.py` | `run(self, context: PipelineContext) -> PipelineContext` |
| `src/runner.py` | Start with `PipelineContext()`; return it |
| `src/tasks/ingest/weather_api.py` | Write via `with_values` |
| `src/tasks/ingest/tides_api.py` | Write via `with_values` |
| `src/tasks/export/weather_parquet.py` | Read via `require` / attributes |
| `src/tasks/export/tides_parquet.py` | Read via `require` / attributes |
| `tests/context/test_pipeline_context.py` | New unit tests for wrapper |
| `tests/tasks/test_*.py` | Pass/assert `PipelineContext` instead of bare dicts |
| `tests/tasks/test_*_live.py` | Same migration for live tests |
| `NextSteps.md` | Mark typed context done / point at next item (optional small doc touch) |

## Implementation steps

1. **TDD — wrapper tests first** — Add `tests/context/test_pipeline_context.py` covering defaults, `with_values` immutability, and `require` success/failure messages.
2. **Implement `PipelineContext`** in `src/context.py` until those tests pass.
3. **Update `BaseTask`** signature to `PipelineContext`.
4. **Migrate ingest tasks** to accept `PipelineContext` and return `context.with_values(...)`.
5. **Migrate export tasks** to use `require` / attributes; keep parquet I/O behaviour unchanged.
6. **Update `TaskRunner`** to initialise and thread `PipelineContext`.
7. **Update unit + live tests** to construct `PipelineContext(...)` and assert attributes.
8. **Validate** with ruff + pytest (non-live).

## Validation

```bash
rtk uv run ruff check ./src ./tests
rtk uv run ruff format --check .
rtk uv run pytest tests/context tests/tasks/test_weather_task.py tests/tasks/test_tides_task.py tests/tasks/test_weather_parquet_task.py tests/tasks/test_tides_parquet_task.py -q
```

(Full `rtk uv run pytest -q` should also pass; live markers remain excluded by default.)

## Risks

- Frozen context means tasks must not mutate nested dicts in place if callers rely on isolation — nested payloads remain mutable dicts (document; do not deep-freeze in this pass).
- Broader signature change touches every task and test — keep behaviour identical beyond the type/API surface.
- `BaseTask` currently names the argument `config`; renaming to `context` is intentional and covered by test updates.

## Approval

- [ ] **waiting** — user has not approved
- [x] **approved** — date: 2026-08-09 (user: "Build")
- [x] **completed** — date: 2026-08-09 (PR #2 on `main`)
