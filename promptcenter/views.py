from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Prompt, PromptVoteCounter
from pathlib import Path
from django.conf import settings
import xml.etree.ElementTree as ET
import json


# Deprecated: home_view no longer used; Hub is the landing page
def home_view(request):
    return render(request, 'pages/hub.html')


def hub_view(request):
    return render(request, 'pages/hub.html')


def contribution_view(request):
    return render(request, 'pages/contribution.html')


def prompts_api(request):
    prompts = list(
        Prompt.objects.values(
            'id', 'title', 'description', 'category', 'role', 'content', 'format'
        )
    )
    return JsonResponse({'prompts': prompts})


def xml_prompts_api(request):
    """Return prompts from fixtures/prompthub.xml as simple objects.
    Uses <task> as title and the <request> XML as full content.
    """
    try:
        # Resolve XML from multiple robust locations
        candidate_paths = [
            Path(__file__).resolve().parent / 'fixtures' / 'prompthub.xml',
            Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'prompthub.xml',
            Path('promptcenter/fixtures/prompthub.xml'),
        ]
        xml_path = next((p for p in candidate_paths if p.exists()), None)
        # Start list and index regardless of XML availability
        items = []
        idx = 1
        if xml_path is not None:
            try:
                tree = ET.parse(str(xml_path))
                root = tree.getroot()
            except ET.ParseError:
                raw = xml_path.read_text(encoding='utf-8')
                root = ET.fromstring(f"<prompts>\n{raw}\n</prompts>")

            for req in root.findall('request'):
                title = (req.findtext('task') or f'Prompt {idx}').strip()
                full_xml = ET.tostring(req, encoding='unicode')
                preview = full_xml[:180] + ('…' if len(full_xml) > 180 else '')

                # extract lightweight tags from request fields
                candidate_tags = []
                for tag_name in ['topic', 'audience', 'style', 'tone', 'language', 'category', 'task']:
                    txt = req.findtext(tag_name)
                    if txt:
                        candidate_tags.append(txt.strip())
                # de-duplicate and trim
                seen = set(); tags = []
                for t in candidate_tags:
                    norm = t[:32]
                    low = norm.lower()
                    if low and low not in seen:
                        seen.add(low)
                        tags.append(norm)

                items.append({
                    'id': idx,
                    'title': title,
                    'category': 'General',
                    'role': '',
                    'preview': preview,
                    'content': full_xml,
                    'tags': tags[:8],
                })
                idx += 1
        # Also merge prompts from fixtures/xml_prompts/ (supports both .json and .xml)
        json_dir_candidates = [
            Path(__file__).resolve().parent / 'fixtures' / 'xml_prompts',
            Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'xml_prompts',
            Path('promptcenter/fixtures/xml_prompts'),
        ]
        json_dir = next((p for p in json_dir_candidates if p.exists()), None)
        if json_dir is not None and json_dir.is_dir():
            processed_stems = set()
            # Process both JSON and XML files in a predictable order
            for fpath in sorted(json_dir.glob('*')):
                if fpath.suffix.lower() == '.json':
                    try:
                        data = json.loads(fpath.read_text(encoding='utf-8') or '{}')
                    except Exception:
                        data = {}
                    title = (data.get('title') or fpath.stem or f'Prompt {idx}').strip()
                    content = str(data.get('prompt') or '')
                    # Fallback to same-stem .xml if JSON lacks content
                    if not content:
                        xml_alt = fpath.with_suffix('.xml')
                        if xml_alt.exists():
                            try:
                                content = xml_alt.read_text(encoding='utf-8')
                            except Exception:
                                content = ''
                    # Fallback to external Prompt folder (one level above BASE_DIR), if present
                    if not content:
                        external_xml = (Path(settings.BASE_DIR).parent / 'Prompt' / f"{fpath.stem}.xml")
                        if external_xml.exists():
                            try:
                                content = external_xml.read_text(encoding='utf-8')
                            except Exception:
                                content = ''
                    if not content:
                        continue
                    preview = content[:180] + ('…' if len(content) > 180 else '')
                    tags = data.get('tags') or []

                    # Try to derive a better title and tags from the XML content
                    try:
                        root_xml = ET.fromstring(content)
                        # Prefer an explicit <title>, then a top-level <task>, then nested ones
                        derived_title = (
                            (root_xml.findtext('title') or '').strip()
                            or (root_xml.findtext('task') or '').strip()
                            or (root_xml.findtext('.//title') or '').strip()
                            or (root_xml.findtext('.//task') or '').strip()
                        )
                        # If our current title is a filename like "xml3" or generic, replace it
                        if derived_title:
                            stem_lower = (fpath.stem or '').lower()
                            if title.lower() in {stem_lower, f'prompt {idx}'.lower()} or title.lower().startswith('xml'):
                                title = derived_title

                        # Build tags if none were provided in JSON
                        if not tags:
                            candidate_tags = []
                            for path in ['role', 'topic', 'audience', 'style', 'tone', 'language', 'category', 'task', './/topic', './/language', './/tone', './/style']:
                                txt = root_xml.findtext(path)
                                if txt:
                                    candidate_tags.append(txt.strip())
                            # De-duplicate while preserving order, trim overly long values
                            seen = set()
                            cleaned = []
                            for t in candidate_tags:
                                tnorm = t[:32]
                                if tnorm and tnorm.lower() not in seen:
                                    seen.add(tnorm.lower())
                                    cleaned.append(tnorm)
                            tags = cleaned[:8]
                    except ET.ParseError:
                        pass

                    # Keep category as "General" regardless of tags per latest direction
                    category = 'General'
                    items.append({
                        'id': idx,
                        'title': title,
                        'category': category,
                        'role': '',
                        'preview': preview,
                        'content': content,
                        'tags': tags,
                    })
                    idx += 1
                    processed_stems.add(fpath.stem.lower())
                elif fpath.suffix.lower() == '.xml':
                    # Skip if already consumed via JSON of same stem
                    if fpath.stem.lower() in processed_stems:
                        continue
                    try:
                        raw = fpath.read_text(encoding='utf-8')
                        # Try to parse title if well-formed
                        try:
                            root = ET.fromstring(raw)
                            tnode = root.find('title') or root.find('task')
                            title = (tnode.text if tnode is not None else fpath.stem) or fpath.stem
                        except ET.ParseError:
                            title = fpath.stem
                        content = raw
                    except Exception:
                        continue
                    preview = content[:180] + ('…' if len(content) > 180 else '')
                    items.append({
                        'id': idx,
                        'title': title.strip(),
                        'category': 'General',
                        'role': '',
                        'preview': preview,
                        'content': content,
                        'tags': [],
                    })
                    idx += 1
        # Merge plaintext prompts from fixtures/plaintext_prompts/ (JSON only)
        try:
            plain_dir_candidates = [
                Path(__file__).resolve().parent / 'fixtures' / 'plaintext_prompts',
                Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'plaintext_prompts',
                Path('promptcenter/fixtures/plaintext_prompts'),
            ]
            plain_dir = next((p for p in plain_dir_candidates if p.exists()), None)
            if plain_dir is not None and plain_dir.is_dir():
                for ppath in sorted(plain_dir.glob('*.json')):
                    try:
                        pdata = json.loads(ppath.read_text(encoding='utf-8') or '{}')
                    except Exception:
                        pdata = {}
                    title = (pdata.get('title') or ppath.stem or f'Prompt {idx}').strip()
                    content = str(pdata.get('prompt') or '')
                    if not content:
                        continue
                    preview = content[:180] + ('…' if len(content) > 180 else '')
                    tags = pdata.get('tags') or []
                    items.append({
                        'id': idx,
                        'title': title,
                        'category': 'General',
                        'role': '',
                        'preview': preview,
                        'content': content,
                        'tags': tags[:8],
                    })
                    idx += 1
        except Exception:
            pass

        if request.GET.get('debug'):
            debug_info = {'count': len(items)}
            debug_info['file'] = str(xml_path) if xml_path is not None else None
            if xml_path is None:
                debug_info['xml_candidates'] = [str(p) for p in candidate_paths]
            return JsonResponse({'prompts': items, 'debug': debug_info})
        # Also merge templates from fixtures/prompt_templates/ (JSON preferred)
        try:
            tmpl_dir_candidates = [
                Path(__file__).resolve().parent / 'fixtures' / 'prompt_templates',
                Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'prompt_templates',
                Path('promptcenter/fixtures/prompt_templates'),
            ]
            tmpl_dir = next((p for p in tmpl_dir_candidates if p.exists()), None)
            if tmpl_dir is not None and tmpl_dir.is_dir():
                for tpath in sorted(tmpl_dir.glob('*')):
                    if tpath.suffix.lower() == '.json':
                        try:
                            data = json.loads(tpath.read_text(encoding='utf-8') or '{}')
                        except Exception:
                            data = {}
                        title = (data.get('title') or tpath.stem or f'Template {idx}').strip()
                        content = str(data.get('prompt') or '')
                        if not content:
                            # Fallback to same-stem XML file if present
                            xml_alt = tpath.with_suffix('.xml')
                            if xml_alt.exists():
                                try:
                                    content = xml_alt.read_text(encoding='utf-8')
                                except Exception:
                                    content = ''
                        if not content:
                            continue
                        preview = content[:180] + ('…' if len(content) > 180 else '')
                        tags = data.get('tags') or []
                        items.append({
                            'id': idx,
                            'title': title,
                            'category': 'Template',
                            'role': 'Template',
                            'preview': preview,
                            'content': content,
                            'tags': tags[:8],
                        })
                        idx += 1
        except Exception:
            pass

        return JsonResponse({'prompts': items})
    except Exception:
        return JsonResponse({'prompts': []})


def xml_prompt_detail(request, pid: int):
    """Render a dedicated page for a single prompt (XML or JSON) by position id.
    The ordering mirrors xml_prompts_api: XML items first (if present), then JSON files.
    """
    try:
        # Build combined items list
        items = []
        idx = 1

        # XML sources
        candidate_paths = [
            Path(__file__).resolve().parent / 'fixtures' / 'prompthub.xml',
            Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'prompthub.xml',
            Path('promptcenter/fixtures/prompthub.xml'),
        ]
        xml_path = next((p for p in candidate_paths if p.exists()), None)
        if xml_path is not None:
            try:
                tree = ET.parse(str(xml_path)); root = tree.getroot()
            except ET.ParseError:
                raw = xml_path.read_text(encoding='utf-8')
                root = ET.fromstring(f"<prompts>\n{raw}\n</prompts>")
            for req in root.findall('request'):
                title = (req.findtext('task') or f'Prompt {idx}').strip()
                content = ET.tostring(req, encoding='unicode')
                items.append({'title': title, 'content': content})
                idx += 1

        # JSON sources
        json_dir_candidates = [
            Path(__file__).resolve().parent / 'fixtures' / 'xml_prompts',
            Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'xml_prompts',
            Path('promptcenter/fixtures/xml_prompts'),
        ]
        json_dir = next((p for p in json_dir_candidates if p.exists()), None)
        if json_dir is not None and json_dir.is_dir():
            for json_path in sorted(json_dir.glob('*.json')):
                try:
                    data = json.loads(json_path.read_text(encoding='utf-8') or '{}')
                except Exception:
                    data = {}
                content = str(data.get('prompt') or '')
                if not content:
                    continue
                title = (data.get('title') or f'Prompt {idx}').strip()
                items.append({'title': title, 'content': content})
                idx += 1

        # Plaintext prompts (fixtures/plaintext_prompts)
        try:
            plain_dir_candidates = [
                Path(__file__).resolve().parent / 'fixtures' / 'plaintext_prompts',
                Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'plaintext_prompts',
                Path('promptcenter/fixtures/plaintext_prompts'),
            ]
            plain_dir = next((p for p in plain_dir_candidates if p.exists()), None)
            if plain_dir is not None and plain_dir.is_dir():
                for ppath in sorted(plain_dir.glob('*.json')):
                    try:
                        pdata = json.loads(ppath.read_text(encoding='utf-8') or '{}')
                    except Exception:
                        pdata = {}
                    content = str(pdata.get('prompt') or '')
                    if not content:
                        continue
                    title = (pdata.get('title') or ppath.stem or f'Prompt {idx}').strip()
                    items.append({'title': title, 'content': content})
                    idx += 1
        except Exception:
            pass

        # Template sources (fixtures/prompt_templates) – mirror xml_prompts_api ordering
        try:
            tmpl_dir_candidates = [
                Path(__file__).resolve().parent / 'fixtures' / 'prompt_templates',
                Path(settings.BASE_DIR) / 'promptcenter' / 'fixtures' / 'prompt_templates',
                Path('promptcenter/fixtures/prompt_templates'),
            ]
            tmpl_dir = next((p for p in tmpl_dir_candidates if p.exists()), None)
            if tmpl_dir is not None and tmpl_dir.is_dir():
                for tpath in sorted(tmpl_dir.glob('*')):
                    if tpath.suffix.lower() == '.json':
                        try:
                            data = json.loads(tpath.read_text(encoding='utf-8') or '{}')
                        except Exception:
                            data = {}
                        content = str(data.get('prompt') or '')
                        if not content:
                            # fallback to XML with same stem
                            xml_alt = tpath.with_suffix('.xml')
                            if xml_alt.exists():
                                try:
                                    content = xml_alt.read_text(encoding='utf-8')
                                except Exception:
                                    content = ''
                        if not content:
                            continue
                        title = (data.get('title') or tpath.stem or f'Template {idx}').strip()
                        items.append({'title': title, 'content': content})
                        idx += 1
        except Exception:
            pass

        if not items:
            return render(request, 'pages/prompt_detail.html', {
                'title': 'Prompt',
                'content': 'Prompt not found',
            })

        # Clamp pid and render
        pos = max(1, min(pid, len(items))) - 1
        sel = items[pos]
        return render(request, 'pages/prompt_detail.html', {
            'title': sel['title'],
            'content': sel['content'],
            'pid': pid,
        })
    except Exception:
        return render(request, 'pages/prompt_detail.html', {
            'title': 'Prompt',
            'content': 'Prompt not found',
            'pid': pid,
        })


def _get_vote_counter(pid: int) -> PromptVoteCounter:
    vc, _ = PromptVoteCounter.objects.get_or_create(prompt_id=pid)
    return vc


def _get_session_vote(request: HttpRequest, pid: int) -> str:
    return (request.session.get('prompt_votes') or {}).get(str(pid)) or ''


def _set_session_vote(request: HttpRequest, pid: int, vote: str) -> None:
    votes = dict(request.session.get('prompt_votes') or {})
    if vote:
        votes[str(pid)] = vote
    else:
        votes.pop(str(pid), None)
    request.session['prompt_votes'] = votes
    try:
        request.session.modified = True
    except Exception:
        pass


@csrf_exempt
def prompt_vote_api(request: HttpRequest, pid: int):
    """Session-scoped vote API. POST {vote: 'up'|'down'|'clear'}
    Returns {upCount, downCount, userVote}.
    """
    try:
        if request.method not in ('GET', 'POST'):
            return JsonResponse({'error': 'method_not_allowed'}, status=405)

        vc = _get_vote_counter(pid)
        if request.method == 'GET':
            return JsonResponse({'upCount': vc.up_count, 'downCount': vc.down_count, 'userVote': _get_session_vote(request, pid)})

        # POST
        try:
            data = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            data = {}
        vote = (data.get('vote') or '').strip().lower()
        if vote not in ('up', 'down', 'clear'):
            return JsonResponse({'error': 'invalid_vote'}, status=400)

        prev = _get_session_vote(request, pid)
        # Adjust counts idempotently
        if vote == 'clear':
            if prev == 'up':
                vc.up_count = max(0, vc.up_count - 1)
            elif prev == 'down':
                vc.down_count = max(0, vc.down_count - 1)
            _set_session_vote(request, pid, '')
        elif vote == 'up':
            if prev == 'down':
                vc.down_count = max(0, vc.down_count - 1)
            if prev != 'up':
                vc.up_count += 1
            _set_session_vote(request, pid, 'up')
        elif vote == 'down':
            if prev == 'up':
                vc.up_count = max(0, vc.up_count - 1)
            if prev != 'down':
                vc.down_count += 1
            _set_session_vote(request, pid, 'down')
        vc.save(update_fields=['up_count', 'down_count'])
        return JsonResponse({'upCount': vc.up_count, 'downCount': vc.down_count, 'userVote': _get_session_vote(request, pid)})
    except Exception:
        return JsonResponse({'error': 'server_error'}, status=500)
