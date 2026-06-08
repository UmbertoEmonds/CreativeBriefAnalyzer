import os
from datetime import datetime

def render_dashboard_template(brief_initial: str, history: list, nb_sources: int, body_content: str) -> str:
    """
    Charge le fichier HTML externe et y injecte dynamiquement les données du State.
    """
    # 1. Génération des sous-parties de texte HTML (ex: historique)
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

    # 2. Localisation et lecture du fichier HTML de template externe
    # Utilise un chemin relatif par rapport à l'emplacement de ce fichier Python
    base_dir = os.path.dirname(__file__)
    template_path = os.path.join(base_dir, "templates", "dashboard.html")

    with open(template_path, "r", encoding="utf-8") as f:
        html_skeleton = f.read()

    # 3. Remplacement des tokens par injection d'un dictionnaire nommé
    return html_skeleton.format(
        current_date=datetime.now().strftime('%d/%m/%Y'),
        current_date_time=datetime.now().strftime('%d/%m/%Y à %H:%M'),
        history_count=len(history),
        nb_sources=nb_sources,
        brief_initial=brief_initial,
        history_html=history_html,
        body_content=body_content
    )