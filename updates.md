## v0.1.0 - Initial setup
- Created Django project `prompthubsite` and app `promptcenter`.
- Added `Prompt` model and admin registration.
- Configured templates and static file settings.
- Implemented pages: Home, Hub, Contribution.
- Implemented prompts API and client-side rendering with copy-to-clipboard.

## v0.2.0 - Semi-automated prompt import system
- Step 1: Created import directories `data/prompts_to_import/` and `data/imported/logs/`.
- Step 2: Established JSON-only import policy for prompt files.
- Step 3: Models updated in `promptcenter/models.py`:
  - Added `Category` model with `name` and `created_at`.
  - Extended `Prompt` with `tags` (JSONField) and `prompt` (TextField) alongside existing fields.
- Step 4: Management command `import_prompts` (in `promptcenter/management/commands/import_prompts.py`) reads JSON files recursively, parses fields (title, tags, description, prompt), ensures categories exist, upserts/skips duplicates, and moves processed files to `data/imported/`.
- Step 5: Added per-run logging to `data/imported/logs/` with counts of added/updated/skipped/duplicates/failed and detailed JSON parsing errors.
- Step 6: Admin updated in `promptcenter/admin.py` to register `Category`, improve search to include `prompt`, and enable filtering by category/format.
- Step 7: Applied migrations to create new fields and `Category`.

### v0.2.1 - Hub reads from DB
- Frontend `staticfiles/hub.js` now fetches from `/api/prompts/` (DB) instead of `/api/xml-prompts/` (fixtures).
- `/api/prompts/` extended to return `tags` and `prompt` fields.
- Detail page `/hub/p/<id>/` now renders by DB `Prompt` id.

How to run the importer
- Place `.json` files into `data/prompts_to_import/` (subfolders allowed).
- Dry run (no DB writes, still logs):
  - `python manage.py import_prompts --dry-run`
- Real import (skip duplicates by default; use `--update-existing` to update):
  - `python manage.py import_prompts`
  - Options: `--pattern '*.json'`, `--source data/prompts_to_import`, `--imported-dir data/imported`, `--update-existing`

Notes
- Duplicate detection checks combinations of title/content/prompt to avoid re-imports.
- Logs are stored under `data/imported/logs/` with timestamps for traceability.