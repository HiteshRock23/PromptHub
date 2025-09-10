from __future__ import annotations

from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from django.db import transaction


def _element_to_compact_xml(elem: ET.Element) -> str:
    xml_str = ET.tostring(elem, encoding='unicode')
    return xml_str.strip()


@transaction.atomic
def import_prompts_from_xml(xml_path: Path) -> int:
    """Import prompts from a simple XML file containing multiple <request> nodes.

    Each <request> becomes one Prompt with:
    - title: value of <task> or "Prompt"
    - description: concatenation of direct child tags and values (excluding large blobs)
    - category: "General"
    - role: ""
    - content: the XML string for the <request> block
    - format: "xml"

    Skips creating duplicates if a prompt with the same content already exists.
    Returns the number of created prompts.
    """
    from .models import Prompt  # local import to avoid AppRegistry issues

    if not xml_path.exists():
        return 0

    # Try to parse. If file has multiple top-level <request> nodes without a
    # single root element, wrap content in a synthetic <prompts> root.
    try:
        tree = ET.parse(str(xml_path))
        root = tree.getroot()
    except ET.ParseError:
        raw = xml_path.read_text(encoding='utf-8')
        wrapped = f"<prompts>\n{raw}\n</prompts>"
        root = ET.fromstring(wrapped)
    created = 0
    for req in root.findall('request'):
        title = (req.findtext('task') or 'Prompt').strip()
        parts: list[str] = []
        for child in list(req):
            if child.tag.lower() == 'task':
                continue
            text = (child.text or '').strip()
            attrs = ' '.join(f"{k}='{v}'" for k, v in child.attrib.items())
            snippet = f"<{child.tag}{(' ' + attrs) if attrs else ''}>" + (text[:80] + ('…' if len(text) > 80 else '')) + f"</{child.tag}>"
            parts.append(snippet)
        description = ' '.join(parts)[:300]

        content_xml = _element_to_compact_xml(req)

        if Prompt.objects.filter(content=content_xml).exists():
            continue

        Prompt.objects.create(
            title=title,
            description=description,
            category='General',
            role='',
            content=content_xml,
            format=Prompt.ContentFormat.XML,
        )
        created += 1
    return created


