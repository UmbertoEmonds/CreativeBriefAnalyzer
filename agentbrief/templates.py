import os
from datetime import datetime
from string import Template
from typing import List


def render_dashboard_template(brief_initial: str, history: list, sources: List[str], body_content: str) -> str:
    """
    Charge le fichier HTML externe et y injecte dynamiquement les données du State via string.Template.
    """
    # 1. Génération de l'historique en HTML
    history_html = ""
    if history:
        for item in history:
            history_html += f"""
            <div class="history-item">
                <div class="history-q">Q: {item['q']}</div>
                <div class="history-a">R: {item['r']}</div>
            </div>
            """
    else:
        history_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune clarification requise.</p>'

    # 2. Génération de la liste des sources cliquables en HTML
    sources_html = ""
    if sources:
        for url in sources:
            display_url = url if len(url) < 45 else url[:42] + "..."
            sources_html += f'<a href="{url}" class="source-link" target="_blank" title="{url}">🔗 {display_url}</a>\n'
    else:
        sources_html = '<p style="font-size: 9.5pt; color: #9ca3af;">Aucune source consultée.</p>'

    # 3. Lecture du template HTML externe
    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, "templates", "dashboard.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html_skeleton = f.read()

    # 4. Utilisation de Template au lieu de .format()
    src = Template(html_skeleton)

    # On passe les variables dans un dictionnaire de substitution
    data = {
        "current_date": datetime.now().strftime('%d/%m/%Y'),
        "current_date_time": datetime.now().strftime('%d/%m/%Y à %H:%M'),
        "history_count": len(history),
        "nb_sources": len(sources),
        "brief_initial": brief_initial,
        "history_html": history_html,
        "sources_html": sources_html,
        "body_content": body_content
    }

    # Remplacement sécurisé des clés commençant par $
    return src.substitute(data)