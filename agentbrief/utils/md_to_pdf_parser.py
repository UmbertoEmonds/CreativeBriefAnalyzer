import re
from fpdf import FPDF


class MarkdownPDFParser:
    """
    Parseur Markdown robuste pour FPDF2.
    Gère les titres (H1, H2, H3), les listes à puces, le gras, l'italique,
    ainsi que les blocs de code (code snippets) avec un fallback pour l'Unicode.
    """

    def __init__(self, pdf: FPDF, font_name: str = "ArialUnicode"):
        self.pdf = pdf
        self.font_name = font_name
        self.max_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin
        self.is_in_code_block = False

    def render_inline_formatting(self, text: str, size: int, line_height: float):
        """
        Découpe le texte par mots, applique le gras (**) et l'italique (*)
        tout en validant manuellement la largeur restante pour éviter les débordements.
        """
        # Découpe le texte en isolant les blocs de **gras** et d'*italique*
        tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)

        for token in tokens:
            if not token:
                continue

            style = ''
            content = token

            if token.startswith('**') and token.endswith('**'):
                style = 'B'
                content = token[2:-2]
            elif token.startswith('*') and token.endswith('*'):
                style = 'I'
                content = token[1:-1]

            try:
                self.pdf.set_font(self.font_name, style=style, size=size)
            except Exception:
                self.pdf.set_font(self.font_name, style='', size=size)

            # Contrôle strict du wrapping par mot (évite le dépassement de page)
            words = content.split(' ')
            for i, word in enumerate(words):
                # Restauration de l'espace supprimé par le split (sauf pour le dernier mot)
                word_to_write = word + ' ' if i < len(words) - 1 else word
                word_width = self.pdf.get_string_width(word_to_write)

                # Si le mot dépasse la marge droite, retour à la ligne forcé
                if self.pdf.get_x() + word_width > (self.pdf.w - self.pdf.r_margin):
                    self.pdf.ln(line_height)
                    if self.pdf.l_margin > self.pdf.init_l_margin:
                        self.pdf.set_x(self.pdf.l_margin)

                self.pdf.write(line_height, word_to_write)

    def parse(self, markdown_text: str):
        """
        Analyse le texte Markdown ligne par ligne et l'injecte dans le PDF.
        """
        self.pdf.init_l_margin = self.pdf.l_margin
        lines = markdown_text.split('\n')

        for line in lines:
            stripped = line.strip()

            # --- 1. Gestion des blocs de code (```) ---
            # Utilisation d'une regex pour intercepter le marqueur même s'il y a un nom de langage (ex: ```python)
            if re.match(r'^```', stripped):
                self.is_in_code_block = not self.is_in_code_block
                if self.is_in_code_block:
                    self.pdf.ln(2)  # Petit espace avant le bloc de code
                else:
                    self.pdf.ln(4)  # Petit espace après le bloc de code
                continue

            # Traitement interne du bloc de code
            if self.is_in_code_block:
                # Utilisation de la police monospace Courier native de FPDF
                self.pdf.set_font("Courier", style='', size=10)

                # Style visuel du bloc de code (Gris foncé sur fond gris clair)
                self.pdf.set_text_color(50, 50, 50)
                self.pdf.set_fill_color(245, 245, 245)

                # Remplacement des caractères "œ" pour éviter le crash de l'encodage latin-1 de Courier
                safe_line = line.replace("œ", "oe").replace("Œ", "Oe")

                # multi_cell avec fill=True applique la couleur d'arrière-plan sur toute la ligne
                self.pdf.multi_cell(0, 5, safe_line, ln=True, fill=True)

                # Restauration de la couleur de texte par défaut
                self.pdf.set_text_color(0, 0, 0)
                continue

            # --- 2. Gestion du Markdown Standard (Hors Code) ---
            self.pdf.set_text_color(0, 0, 0)

            if not stripped:
                self.pdf.ln(4)
                continue

            # Élimination des lignes de soulignement Markdown (ex: === ou --- sous un titre)
            if re.match(r'^={3,}$', stripped) or re.match(r'^-{3,}$', stripped):
                continue

            # Titres H1 (# )
            if stripped.startswith('# '):
                self.pdf.ln(6)
                self.pdf.set_font(self.font_name, style='', size=18)
                self.pdf.multi_cell(0, 10, stripped[2:], ln=True)
                self.pdf.ln(2)

            # Titres H2 (## )
            elif stripped.startswith('## '):
                self.pdf.ln(5)
                self.pdf.set_font(self.font_name, style='', size=14)
                self.pdf.multi_cell(0, 8, stripped[3:], ln=True)
                self.pdf.ln(2)

            # Titres H3 (### )
            elif stripped.startswith('### '):
                self.pdf.ln(4)
                self.pdf.set_font(self.font_name, style='', size=12)
                self.pdf.multi_cell(0, 7, stripped[4:], ln=True)
                self.pdf.ln(1)

            # Listes à puces (* ou -)
            elif stripped.startswith('* ') or stripped.startswith('- '):
                # Nettoyage des caractères de puces du prompt et des espaces insécables (\xa0)
                content = re.sub(r'^[\*\-\s\xa0]+', '', line)

                orig_margin = self.pdf.init_l_margin
                self.pdf.set_x(orig_margin + 5)
                self.pdf.set_font(self.font_name, style='', size=11)
                self.pdf.write(6, "• ")

                # Décalage de la marge gauche pour aligner proprement les retours à la ligne de la puce
                self.pdf.set_left_margin(orig_margin + 12)
                self.pdf.set_x(orig_margin + 12)

                self.render_inline_formatting(content, size=11, line_height=6)
                self.pdf.ln(6)

                # Réinitialisation de la marge initiale
                self.pdf.set_left_margin(orig_margin)

            # Paragraphes normaux
            else:
                self.render_inline_formatting(stripped, size=11, line_height=6)
                self.pdf.ln(6)