"""
Markdown to HTML converter for the ChatBotLangGraph fiche generation.

Pipeline :
  1. _preprocess()  — filet de sécurité qui corrige les patterns LLM cassés
  2. mistune         — parser Markdown robuste (remplace python-markdown)

Dépendance : pip install mistune
"""

import re
import mistune


# ── Sections dont les lignes nues deviennent des items de liste ───────────────
# Correspond aux headers H1-H6 annonçant une section "takeaways".
_BULLET_SECTION_RE = re.compile(
    r'^#{1,6}\s+.*(points?\s+[àa]\s+retenir|key\s+takeaway|à\s+retenir)',
    re.IGNORECASE,
)

# Même pattern, mais pour les lignes qui ne commencent PAS par # (ex : "Points à retenir")
_BULLET_SECTION_BARE_RE = re.compile(
    r'^(?:\*\*)?(?:points?\s+[àa]\s+retenir|key\s+takeaways?|à\s+retenir)[\s:]*(?:\*\*)?$',
    re.IGNORECASE,
)


def _strip_list_item_backticks(s: str) -> str:
    """
    Fix 3 — Backticks inline utilisés à tort pour entourer un item de liste entier.

    Le LLM écrit parfois :  * `- Mon point à retenir.`
    ou :                     - `Du texte ordinaire`
    alors que les backticks sont réservés au code inline (`variable`, `fn()`).

    Règle : si TOUT le contenu d'un item de liste (après le marqueur -/*/ numéro)
    est enveloppé dans une paire de backticks, on les retire.
    On ne touche PAS aux backticks partiels (ex : "voir `config.py` pour les détails").
    """
    # Matcher : marqueur de liste + espace + `contenu complet`
    m = re.match(r'^([-*+]|\d+\.)\s+`([^`]+)`\s*$', s)
    if m:
        return f'{m.group(1)} {m.group(2)}'
    return s


def _preprocess(text: str) -> str:
    """
    Filet de sécurité pour Markdown généré par LLM.

    Corrige cinq patterns non-ambigus et sans risque de faux positifs :

    Fix 1 — Listes inline dans un paragraphe
        LLM : "Intro : - Item A - Item B - Item C"  (tout sur une ligne)
        Résultat : intro + <ul> propre
        Condition stricte : ≥ 3 segments ET l'intro se termine par ':', '.', ')'
        → évite de toucher "valeur A - valeur B" ou "cmd - opt - esc"

    Fix 2 — Lignes nues sous un header "Points à retenir"
        LLM : phrases sans '- ' en début de ligne
        Résultat : items de liste propres

    Fix 3 — Backticks inline autour d'items de liste entiers
        LLM : "* `- Mon point.`"  ou  "- `Texte ordinaire`"
        Résultat : item de liste propre, sans <code>

    Fix 4 — Espace manquant après les marqueurs `#`
        LLM : "###Sous-titre" (sans espace après ###)
        Résultat : "### Sous-titre" (valide pour le parser Markdown)

    Fix 5 — En-tête "Points à retenir" sans marqueur `##`
        LLM : "Points à retenir" au lieu de "## Points à retenir"
        Résultat : la section est correctement détectée comme liste à puces

    Les code fences (``` … ```) sont toujours préservées intactes.
    """
    lines = text.split('\n')
    out: list[str] = []
    in_code = False
    in_bullet_section = False

    for line in lines:
        s = line.strip()

        # ── Protéger les blocs de code ────────────────────────────────────────
        if s.startswith('```'):
            in_code = not in_code
            out.append(line)
            continue
        if in_code:
            out.append(line)
            continue

        # ── Classifier la ligne ───────────────────────────────────────────────
        is_heading   = s.startswith('#')
        is_list_item = bool(re.match(r'^[-*+]\s', s)) or bool(re.match(r'^\d+\.\s', s))
        is_hr        = bool(re.match(r'^[-*_]{3,}$', s))
        is_empty     = s == ''

        # ── Fix 4 : espace manquant après les # (ex: "###Nœuds" -> "### Nœuds") ─
        m = re.match(r'^(#{1,6})([^\s#])', s)
        if m:
            s = m.group(1) + ' ' + s[m.end(1):]
            line = s
            is_heading = True  # reclassify as heading after fix

        # Mémoriser si on est dans une section "bullet"
        if is_heading:
            in_bullet_section = bool(_BULLET_SECTION_RE.match(s))
            out.append(line)
            continue

        # ── Fix 5 : en-tête "Points à retenir" sans ## (ex: "Points à retenir") ─
        if not is_list_item and not is_hr and not is_empty:
            if _BULLET_SECTION_BARE_RE.match(s):
                in_bullet_section = True
                out.append(line)
                continue

        # ── Fix 1 : liste inline ──────────────────────────────────────────────
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

        # ── Fix 2 : lignes nues dans une section "Points à retenir" ──────────
        if in_bullet_section and not is_empty and not is_list_item and not is_hr:
            out.append(f'- {s}')
            continue

        # ── Fix 3 : backticks autour d'un item de liste entier ───────────────
        if is_list_item:
            out.append(_strip_list_item_backticks(s))
            continue

        # Sortir de la section "Points à retenir" sur ligne blanche
        if is_empty:
            in_bullet_section = False

        out.append(line)

    return '\n'.join(out)


# Créer le renderer mistune une seule fois (thread-safe, réutilisable)
_md_render = mistune.create_markdown(
    plugins=['table', 'strikethrough', 'footnotes', 'url'],
)


def markdown_to_html(markdown_text: str) -> str:
    """
    Convertit du Markdown en HTML.

    Applique d'abord un pré-traitement pour corriger les patterns LLM cassés,
    puis utilise mistune pour un rendu robuste.

    Args:
        markdown_text: Contenu Markdown brut à convertir.

    Returns:
        str: HTML généré.
    """
    if not markdown_text:
        return "<p>Aucun contenu généré.</p>"

    return _md_render(_preprocess(markdown_text))