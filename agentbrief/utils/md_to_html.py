"""Markdown to HTML converter with LLM output safety preprocessing."""
import re
import mistune


_BULLET_SECTION_RE = re.compile(
    r'^#{1,6}\s+.*(points?\s+[àa]\s+retenir|key\s+takeaway|à\s+retenir)',
    re.IGNORECASE,
)

_BULLET_SECTION_BARE_RE = re.compile(
    r'^(?:\*\*)?(?:points?\s+[àa]\s+retenir|key\s+takeaways?|à\s+retenir)[\s:]*(?:\*\*)?$',
    re.IGNORECASE,
)


def _strip_list_item_backticks(s: str) -> str:
    """Remove backticks incorrectly wrapping an entire list item."""
    m = re.match(r'^([-*+]|\d+\.)\s+`([^`]+)`\s*$', s)
    if m:
        return f'{m.group(1)} {m.group(2)}'
    return s


def _preprocess(text: str) -> str:
    """Fix broken LLM Markdown patterns: inline lists, bare bullet lines, missing spaces, backtick abuse."""
    lines = text.split('\n')
    out: list[str] = []
    in_code = False
    in_bullet_section = False

    for line in lines:
        s = line.strip()

        if s.startswith('```'):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue

        is_heading   = s.startswith('#')
        is_list_item = bool(re.match(r'^[-*+]\s', s)) or bool(re.match(r'^\d+\.\s', s))
        is_hr        = bool(re.match(r'^[-*_]{3,}$', s))
        is_empty     = s == ''

        m = re.match(r'^(#{1,6})([^\s#])', s)
        if m:
            s = m.group(1) + ' ' + s[m.end(1):]
            line = s
            is_heading = True

        if is_heading:
            in_bullet_section = bool(_BULLET_SECTION_RE.match(s))
            out.append(line)
            continue

        if not is_list_item and not is_hr and not is_empty:
            if _BULLET_SECTION_BARE_RE.match(s):
                in_bullet_section = True
                out.append(line)
                continue

        if not is_list_item and not is_hr and not is_empty:
            parts = re.split(r'\s+-\s+(?=[A-ZÀ-ÿa-z0-9\(«"»"])', s)
            intro_ends_as_label = bool(re.search(r'[:.)\]]$', parts[0].rstrip()))
            if len(parts) >= 3 and intro_ends_as_label:
                intro = parts[0].rstrip(' ').rstrip(':.,)').strip()
                items = [p.strip() for p in parts[1:] if p.strip()]
                out.append(intro + ' :')
                out.append('')
                for item in items:
                    out.append(f'- {item}')
                out.append('')
                continue

        if in_bullet_section and not is_empty and not is_list_item and not is_hr:
            out.append(f'- {s}')
            continue

        if is_list_item:
            out.append(_strip_list_item_backticks(s))
            continue

        if is_empty:
            in_bullet_section = False

        out.append(line)

    return '\n'.join(out)


_md_render = mistune.create_markdown(
    plugins=['table', 'strikethrough', 'footnotes', 'url'],
)


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML with LLM output safety preprocessing."""
    if not markdown_text:
        return "<p>Aucun contenu généré.</p>"

    return _md_render(_preprocess(markdown_text))
