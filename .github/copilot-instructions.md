<!-- Generated/updated by assistant: please review and iterate -->
# Copilot / AI agent instructions for the `weather` repo

Purpose
- This repository is named `weather` and currently contains a short README describing a project to "Ingest weather data from open APIs." The default branch is `main`.

Current state (facts you can rely on)
- Only discoverable file: `README.md` (project purpose).
- Repo owner: pythonPansy; branch: `main`.

Primary guidance for automated changes
- Do not scaffold large systems or pick a language/framework without asking the human owner first. The repo has no obvious language, packaging, or test layout.
- If asked to create code, propose a minimal plan (stack, directory layout, dependencies) and request explicit confirmation before committing files.

If you are asked to implement an ingestion pipeline (recommended minimal workflow)
- Propose a concrete stack in the PR description. Example minimal Python scaffold: `src/` for modules, `tests/` for tests, `requirements.txt` or `pyproject.toml` for dependencies.
- Example PR summary: "Add minimal Python ingestion scaffold using `requests` and `pytest` — implements basic fetch from sample API, local JSON output, and one unit test."

Repository conventions to follow when adding code
- Use `src/` for runtime packages and `tests/` for unit tests.
- Keep single-responsibility modules (one small module per file) and small functions to ease review.
- Use explicit dependency files: `pyproject.toml`. Do not add dependencies without listingand pinning them.

Branching & commits
- Base branch is `main`. Create feature branches as `feature/<short-desc>` or `fix/<short-desc>` for small fixes.
- Make small, focused commits with descriptive messages (imperative tense). Put rationale in PR description when introducing new architecture.

What to check in code reviews (automation hints)
- Ensure new code includes a README section explaining how to run locally (install, run, test).
- Ensure tests run via a simple command such as `pytest` (if Python) or the appropriate test runner for the chosen stack.
- Ensure any external API keys or secrets are NOT committed — use environment variables and document expected env vars.
- PEP 8 compliance for Python code; consistent code style for other languages.
- Ensure dependencies are listed and pinned in the appropriate file.
- YAML should be properly indented; JSON should be well-formed. Both should follow best practices and use a linter if possible.

When you cannot discover the answer in this repo
- Ask the repository owner one clarifying question before making decisions that change the project's language, storage, or CI.
- Example questions to ask the owner: "Which runtime would you prefer (Python/Node/Go)?", "Do you want ingestion results stored in a DB or as files?", "Any preferred CI provider or test matrix?"

References
- Project README: [README.md](README.md)

If this file already existed, merge strategy
- Preserve any explicit human-written instructions. If this file exists, prefer the repository maintainer's text and only add missing facts (e.g., default branch) or a small note that the repo currently lacks a language/runtime.

Ask for feedback
- After making changes, request a short review from the owner describing whether the chosen stack and scaffold meet expectations.