# PromptHub

A minimal prompt library built with Django and vanilla HTML/CSS/JS.

## Tech Stack
- Backend: Django
- Frontend: HTML, CSS, JavaScript (no frontend frameworks)

## Quickstart

1. Create and activate a virtual environment (Windows PowerShell):
```
python -m venv venv
./venv/Scripts/Activate.ps1
```
2. Install dependencies:
```
pip install django
```
3. Initialize database and run:
```
python manage.py migrate
python manage.py runserver
```
4. Visit:
- Home: http://127.0.0.1:8000/
- Hub: http://127.0.0.1:8000/hub/
- Contribute: http://127.0.0.1:8000/contribute/
- API: http://127.0.0.1:8000/api/prompts/

## App Structure
- `prompthubsite/` – project settings and root URLs
- `promptcenter/` – app for prompts (models, views, urls)
- `templates/pages/` – HTML templates
- `staticfiles/` – global CSS and JS

## Prompt Model
- `title`, `description`, `category`, `role` (optional)
- `content` (text of the prompt)
- `format` (plain, json, xml)

## Contribution
Open a Pull Request with your prompts or improvements. See `templates/pages/contribution.html` for guidance.

## Future Scope
- Search and filtering on Hub
- Pagination and categories
- Tagging and ratings
- Export prompts (JSON)
