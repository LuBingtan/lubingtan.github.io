# Repository Guidelines

## Project Structure & Module Organization
This repository is an `mdBook`-based wiki.
- `src/`: book source files.
- `src/docs/`: main documentation content (grouped by domain such as `Cloud_Native`, `Machine_Learning`, `Operation`).
- `src/SUMMARY.md`: generated table of contents.
- `tools/`: helper scripts (`gen-summary.py`, `blog-preprocessor.py`).
- `book/`: generated output site.
- `bin/`: local tool binaries and debug artifacts.
- `.github/workflows/gh-pages.yml`: CI build and deploy workflow.

## Build, Test, and Development Commands
Use `make` targets as the canonical interface:
- `make mdbook`: downloads `mdbook` to `./bin` if missing.
- `make gen-summary`: regenerates `src/SUMMARY.md` from `src/docs`.
- `make build`: runs summary generation and builds static site into `./book`.
- `make serve`: serves the book locally for preview.

Example local loop:
```bash
make build
make serve
```

## Coding Style & Naming Conventions
- Markdown: keep headings hierarchical, use concise section titles, and prefer relative links.
- Python scripts in `tools/`: follow PEP 8 style (4-space indentation, `snake_case` names, clear function boundaries).
- File and directory naming in docs: prefer descriptive names; existing mixed English/Chinese names are acceptable and should stay consistent with surrounding content.
- Avoid manual edits to generated `src/SUMMARY.md`; regenerate via `make gen-summary`.

## Testing Guidelines
There is no dedicated unit test suite currently. Validation is build-based:
- Run `make build` before opening a PR.
- Confirm `make serve` renders pages and links correctly.
- If editing `tools/*.py`, validate by regenerating summary and checking output diffs.

## Commit & Pull Request Guidelines
Commit history favors short, imperative messages (for example: `fix blog preprocessor script`, `move docs to src dir`).
- Keep subject lines concise and action-oriented.
- Group related docs/script changes in one commit.

For pull requests:
- Include a short summary of content/script changes.
- Link related issues when applicable.
- Add screenshots for visible rendering/navigation changes.
- Ensure CI (`make build` in GitHub Actions) passes.
