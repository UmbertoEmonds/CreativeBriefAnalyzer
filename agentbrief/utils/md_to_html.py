import re


def markdown_to_html(markdown_text: str) -> str:
    """
    Convertit le Markdown en HTML ligne par ligne.
    Garantit l'isolation complète des blocs de code Python.
    """
    if not markdown_text:
        return "<p>Aucun contenu généré.</p>"

    lines = markdown_text.split('\n')
    html_lines = []
    in_code_block = False

    for line in lines:
        # ---- GESTION DES BLOCS DE CODE ----
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                html_lines.append('<pre><code>')
            else:
                in_code_block = False
                html_lines.append('</code></pre>')
            continue

        # Si on est dans un bloc de code, on n'interprète rien
        if in_code_block:
            safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(safe_line)
            continue

        # ---- GESTION DU MARKDOWN CLASSIQUE ----
        # Titres
        if line.startswith('# '):
            line = f'<h1 class="fiche-title">{line[2:]}</h1>'
        elif line.startswith('## '):
            line = f'<h2>{line[3:]}</h2>'
        elif line.startswith('### '):
            line = f'<h3>{line[4:]}</h3>'

        # Listes
        elif line.strip().startswith('- '):
            line = f'<li>{line.strip()[2:]}</li>'
        elif line.strip().startswith('* '):
            line = f'<li>{line.strip()[2:]}</li>'
        elif re.match(r'^[0-9]+\.\s', line.strip()):
            content = re.sub(r'^[0-9]+\.\s', '', line.strip())
            line = f'<li>{content}</li>'

        # Gras, Italique, Code inline
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', line)
        line = re.sub(r'`(.*?)`', r'<code>\1</code>', line)

        # Paragraphes
        if line.strip() and not line.strip().startswith('<h') and not line.strip().startswith('<li'):
            line = f'<p>{line}</p>'

        html_lines.append(line)

    return '\n'.join(html_lines)