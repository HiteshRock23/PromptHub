from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from promptcenter.models import Prompt, Category


def _ensure_directories(source_dir: Path, imported_dir: Path) -> None:
    source_dir.mkdir(parents=True, exist_ok=True)
    imported_dir.mkdir(parents=True, exist_ok=True)
    (imported_dir / 'logs').mkdir(parents=True, exist_ok=True)


def _iter_json_files(root: Path, pattern: str) -> Iterable[Path]:
    pattern = pattern or '*.json'
    for path in sorted(root.rglob(pattern)):
        if path.is_file() and path.suffix.lower() == '.json':
            yield path


def _normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip()[:64] for v in value if str(v).strip()]
    if isinstance(value, str):
        return [t.strip()[:64] for t in value.split(',') if t.strip()]
    return []


def _safe_move_to_imported(file_path: Path, source_root: Path, imported_root: Path) -> Path:
    rel = file_path.relative_to(source_root)
    dest = imported_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        dest = dest.with_name(f"{dest.stem}_{ts}{dest.suffix}")
    shutil.move(str(file_path), str(dest))
    return dest


class Command(BaseCommand):
    help = 'Import prompt JSON files from data/prompts_to_import into the database.'

    def add_arguments(self, parser: CommandParser) -> None:
        base_data = Path(settings.BASE_DIR) / 'data'
        parser.add_argument(
            '--source',
            type=Path,
            default=base_data / 'prompts_to_import',
            help='Directory to scan for prompt files (recursive).',
        )
        parser.add_argument(
            '--imported-dir',
            type=Path,
            default=base_data / 'imported',
            help='Directory to move processed files into (mirrors tree).',
        )
        parser.add_argument(
            '--pattern',
            type=str,
            default='*.json',
            help='Glob pattern to match files under source.',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing prompts when duplicates are found (default skips).',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and report without writing to DB or moving files.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source_dir: Path = options['source']
        imported_dir: Path = options['imported_dir']
        pattern: str = options['pattern']
        update_existing: bool = options['update_existing']
        dry_run: bool = options['dry_run']

        _ensure_directories(source_dir, imported_dir)

        # Configure logging per session
        log_dir = imported_dir / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        logfile = log_dir / f'import_{ts}.log'

        logger = logging.getLogger('prompt_import')
        logger.setLevel(logging.INFO)
        logger.handlers = []
        fh = logging.FileHandler(logfile, encoding='utf-8')
        sh = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        fh.setFormatter(fmt)
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)

        added = 0
        updated = 0
        skipped = 0
        failed = 0
        duplicates = 0
        processed_files = 0

        json_files = list(_iter_json_files(source_dir, pattern))
        if not json_files:
            logger.info('No JSON files found in %s', source_dir)
            logger.info('Log file: %s', logfile)
            return

        logger.info('Starting import. Files discovered: %d', len(json_files))

        for fpath in json_files:
            try:
                raw = fpath.read_text(encoding='utf-8')
                data = json.loads(raw)
            except Exception as e:
                failed += 1
                logger.error('JSON parse error: %s | file=%s', e, fpath)
                # Move even failed files to avoid reprocessing unless dry-run
                if not dry_run:
                    _safe_move_to_imported(fpath, source_dir, imported_dir)
                continue

            items: list[dict[str, Any]]
            if isinstance(data, dict):
                items = [data]
            elif isinstance(data, list):
                items = [d for d in data if isinstance(d, dict)]
                if not items:
                    logger.warning('No valid prompt objects in list file: %s', fpath)
            else:
                logger.warning('Unsupported JSON root type in %s; skipping', fpath)
                if not dry_run:
                    _safe_move_to_imported(fpath, source_dir, imported_dir)
                continue

            any_success = False

            for obj in items:
                title = (str(obj.get('title') or '')).strip() or fpath.stem
                prompt_text = str(obj.get('prompt') or obj.get('content') or '').strip()
                if not prompt_text:
                    failed += 1
                    logger.error('Missing prompt text; skipping object | file=%s title=%s', fpath, title)
                    continue
                description = str(obj.get('description') or '').strip()
                tags = _normalize_tags(obj.get('tags'))
                category_name = str(obj.get('category') or 'General').strip() or 'General'
                role = str(obj.get('role') or '').strip()

                try:
                    if dry_run:
                        # Validate only
                        _ = Category(name=category_name)
                        _ = Prompt(
                            title=title,
                            description=description,
                            category=category_name,
                            role=role,
                            tags=tags,
                            prompt=prompt_text,
                            content=prompt_text,
                            format=Prompt.ContentFormat.JSON,
                        )
                        skipped += 1
                        continue

                    with transaction.atomic():
                        # Ensure category exists (by name) for reference in admin
                        Category.objects.get_or_create(name=category_name)

                        existing = (
                            Prompt.objects.filter(title=title, prompt=prompt_text).first()
                            or Prompt.objects.filter(content=prompt_text).first()
                            or Prompt.objects.filter(title=title, content=prompt_text).first()
                        )
                        if existing:
                            duplicates += 1
                            if update_existing:
                                existing.description = description or existing.description
                                existing.category = category_name
                                existing.role = role or existing.role
                                existing.tags = tags or existing.tags
                                existing.prompt = prompt_text or existing.prompt
                                existing.content = prompt_text or existing.content
                                existing.format = Prompt.ContentFormat.JSON
                                existing.save()
                                updated += 1
                                any_success = True
                                logger.info('Updated existing prompt: %s', title)
                            else:
                                skipped += 1
                                logger.info('Skipped duplicate prompt: %s', title)
                            continue

                        Prompt.objects.create(
                            title=title,
                            description=description,
                            category=category_name,
                            role=role,
                            tags=tags,
                            prompt=prompt_text,
                            content=prompt_text,
                            format=Prompt.ContentFormat.JSON,
                        )
                        added += 1
                        any_success = True
                        logger.info('Added prompt: %s', title)
                except Exception as e:  # noqa: BLE001
                    failed += 1
                    logger.exception('Failed to save prompt | file=%s title=%s err=%s', fpath, title, e)

            if not dry_run:
                _safe_move_to_imported(fpath, source_dir, imported_dir)
                processed_files += 1
            else:
                processed_files += 1

        logger.info('Import complete. files=%d added=%d updated=%d skipped=%d dupes=%d failed=%d',
                    processed_files, added, updated, skipped, duplicates, failed)
        logger.info('Log file: %s', logfile)


