# Contributing to Weather

Thank you for your interest in contributing! This document outlines the development workflow, code standards, and requirements for this project.

## Development Workflow

### Feature Branch and Pull Request Workflow

**All changes MUST follow this workflow:**

1. **Create a feature branch** from `main`
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<descriptive-name>
   # or
   git checkout -b fix/<descriptive-name>
   ```

2. **Make your changes** following the code standards below

3. **Test your changes**
   ```bash
   uv run pytest -q
   uv run ruff check ./src ./tests
   uv run ruff format --check .
   ```

4. **Commit your changes** with clear, descriptive messages
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```

5. **Push your branch**
   ```bash
   git push -u origin feature/<your-branch-name>
   ```

6. **Create a Pull Request** on GitHub
   - Base branch: `main`
   - Provide a clear description of changes
   - Reference any related issues
   - Wait for review and approval

7. **Never commit directly to `main`** - all changes must go through a PR

### Branch Naming Conventions

- Feature branches: `feature/<short-description>`
- Bug fixes: `fix/<short-description>`
- Documentation: `docs/<short-description>`

Use lowercase with hyphens, e.g., `feature/add-tide-api`, `fix/datetime-parsing`

## Code Standards

### UK English

**All code, documentation, and identifiers MUST use UK English spelling.**

Required spellings:
- `licence` (not license)
- `colour` (not color)
- `behaviour` (not behavior)
- `metre/metres` (not meter/meters)
- `organise` (not organize)
- `normalise` (not normalize)

This applies to:
- Variable and function names
- Comments and docstrings
- API field names
- Documentation
- Commit messages

**Exception:** External library/API identifiers that cannot be changed (e.g., `timezone` in Python stdlib)

### Python Code Style

- **Python version**: 3.11+
- **Type hints**: Required on all public APIs
- **Line length**: 88 characters (Black/Ruff default)
- **Linting**: Ruff (configured in `pyproject.toml`)
- **Formatting**: Ruff format

### Linting and Formatting

#### Automatic Linting (Cursor Hooks)

This project uses Cursor hooks for automatic linting:

- **After file edit**: Runs `ruff check --fix` and `ruff format` on edited Python files
- **On stop**: Runs ruff on all agent-edited files in git diff

The hooks are configured in `.cursor/hooks.json` and run automatically in Cursor IDE.

#### Manual Linting

Run before committing:

```bash
# Check for issues
uv run ruff check ./src ./tests

# Auto-fix issues
uv run ruff check --fix ./src ./tests

# Check formatting
uv run ruff format --check .

# Apply formatting
uv run ruff format .
```

#### Pre-commit Hooks (Optional)

Pre-commit is configured but cannot be installed when using Cursor's hook system. To run pre-commit checks manually:

```bash
uv run pre-commit run --all-files
```

## Testing Requirements

### Running Tests

All tests must pass before creating a PR:

```bash
# Run all tests (excludes live API tests by default)
uv run pytest -q

# Run specific test directory
uv run pytest tests/api/ -q

# Run with verbose output
uv run pytest -v

# Run live API tests (requires API keys)
uv run pytest -m live_api
```

### Test Coverage

- **Unit tests**: Required for all new functionality
- **Integration tests**: Required for API endpoints and task pipelines
- **Live API tests**: Mark with `@pytest.mark.live_api` for tests requiring external APIs
- **Mocking**: Mock external API calls in unit tests using `pytest-mock`

### Writing Tests

- Place tests in `tests/` directory mirroring `src/` structure
- Use descriptive test function names: `test_<what>_<when>_<expected>`
- Example: `test_get_tides_invalid_location_returns_404`

## API Development

### REST API Standards

When developing API endpoints:

1. **Use Pydantic models** for request/response validation
2. **Return appropriate HTTP status codes**:
   - 200: Success
   - 400: Bad request (validation error)
   - 404: Not found
   - 500: Internal server error
3. **Use UK English** in field names and documentation
4. **Document endpoints** with docstrings (automatic OpenAPI docs)

### API Testing

- Test with FastAPI `TestClient`
- Mock external services
- Test error cases (404, 400, 500)
- Validate response schemas

## Documentation

### Code Documentation

- **Docstrings**: Required for all public classes, functions, and methods
- **Format**: Google-style docstrings
- **Type hints**: Use type hints instead of documenting types in docstrings

Example:

```python
def classify_tide_phase(height: float, is_high: bool) -> str | None:
    """Classify tide phase based on height.
    
    Args:
        height: Tide height in metres
        is_high: True if high tide, False if low tide
        
    Returns:
        "spring", "neap", "medium", or None if unavailable
    """
```

### README Updates

Update the README when adding:
- New features or functionality
- New dependencies
- New API endpoints
- Configuration changes

## Dependencies

### Adding Dependencies

Add dependencies to `pyproject.toml`:

```toml
dependencies = [
    "package-name>=1.0.0",
]
```

Never specify exact versions for flexibility; use `>=` with minimum version.

### Development Dependencies

Add dev dependencies to the appropriate group:

```toml
[dependency-groups]
dev = [
    { include-group = "lint" },
    { include-group = "test" },
]
lint = [
    "ruff~=0.8.0",
]
test = [
    "pytest~=7.4.0",
]
```

### Syncing Dependencies

After adding dependencies:

```bash
uv sync --group dev
```

## Git Commit Messages

Write clear, descriptive commit messages:

```
Brief summary (50 chars or less) in UK English

More detailed explanation if needed. Wrap at 72 characters.
Explain what and why, not how (code shows how).

- Bullet points are okay
- Use hyphens for bullets
```

Example:

```
Add REST API endpoints for tide predictions

- Implement GET /api/locations endpoint
- Implement GET /api/tides/{location_id} endpoint  
- Add tide phase classification (spring/neap/medium)
- Include comprehensive unit tests
```

## Code Review

Pull requests will be reviewed for:

- ✅ All tests pass
- ✅ Linting checks pass
- ✅ UK English used throughout
- ✅ Code is well-documented
- ✅ Changes are made on a feature branch
- ✅ No direct commits to `main`

## Environment Setup

### Initial Setup

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync --group dev

# Run tests
uv run pytest -q
```

### Cursor IDE Setup

This project includes Cursor hooks for automatic linting. Ensure:

1. `.cursor/hooks.json` is present
2. Cursor IDE recognizes the hooks (check Settings → Hooks)
3. `uv` is available in PATH

## Questions?

For questions or issues:

- Create a GitHub issue with the `question` label
- Check existing issues and documentation first
- Provide minimal reproducible examples for bugs

## AI-Assisted Development

This project uses a compound engineering workflow with AI assistance. See:

- `docs/ai_assisted_development.md` - Workflow details
- `.cursor/rules/` - Agent rules and guidelines

When working with AI agents, ensure they follow the same standards outlined in this document.
