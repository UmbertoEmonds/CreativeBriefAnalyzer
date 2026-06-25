"""Graph node implementations: call_model, ask, retrieve, generate_final_data, create_html."""
from langgraph.types import interrupt
from langchain_core.prompts import ChatPromptTemplate
from agentbrief.rag import build_retriever
from agentbrief.state import BriefState, QA
from langchain_tavily import TavilySearch
from datetime import datetime
import os

from agentbrief.templates import render_dashboard_template
from agentbrief.utils.md_to_html import markdown_to_html
from agentbrief.config import MAX_KEYWORDS, TAVILY_MAX_RESULTS, TAVILY_INPUT_LIMIT, MAX_OUTPUT_FILES, MAX_INPUT_LENGTH


_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un assistant expert dans l'analyse de briefs de projets. Ton role est de verifier si le brief contient les informations fondamentales necessaires pour commencer la redaction.

Le livrable final est toujours un dashboard HTML pedagogique. Ne pose donc jamais de question sur le format attendu.

## DONNEES
Brief a analyser : {user_input}
Historique des clarifications : {history_plain}

## DIRECTIVES STRICTES DE SECURITE :
- NE TENTE JAMAIS de definir, de developper, d'interpreter ou de deviner le sens des acronymes, des sigles, du jargon ou des termes specifiques au domaine du brief. Traite-les comme des concepts opaques sans chercher a les expliciter a ce stade.
- Concentre-toi exclusivement sur la structure du besoin : Sait-on a QUI s'adresse ce projet ? Sait-on QUEL est le but precis recherche ?

## GESTION DE L'HISTORIQUE DES CLARIFICATIONS :
- Chaque question deja posee et respondue dans l'historique doit etre consideree comme une information desormais acquise, meme si la reponse est partielle.
- Si une information fondamentale (public cible, objectif) a deja fait l'objet d'une question dans l'historique, ne la signale plus comme manquante.
- Identifie UNIQUEMENT les informations fondamentales qui n'ont PAS encore ete abordees dans l'historique.

Si le brief manque d'informations fondamentales pour commencer la redaction et que ces informations n'ont PAS encore ete demandees dans l'historique, commence ta reponse EXACTEMENT par le mot-cle : CLARIFICATION_NEEDED, suivi d'une breve justification de ce qui manque.
Sinon, fais directement une analyse complete de la demande.""")
])

_QUESTION_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un analyste rigoureux. Pose UNE SEULE question a l'utilisateur pour combler le manque identifie dans l'analyse ci-dessous.

Analyse du brief : {analyse}

## REGLES STRICTES :
- INTERDICTION TOTALE de definir, de deviner, d'etendre ou d'expliciter le sens des acronymes, abreviations ou expressions specifiques utilises dans le brief.
- Ne repose pas une question sur une information deja fournie dans le brief utilisateur ({user_input}) ou deja abordee dans l'historique des clarifications.
- Ne demande pas le format de livrable (le systeme ne genere que du HTML).
- Formule une question unique courte et directe.
- Si tu mentionnes un terme issu du brief, utilise-le BRUT, sans l'expliquer.

Genere UNIQUEMENT la question, sans preambule.""")
])

_KEYWORD_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Extrais UNIQUEMENT les mots-cles techniques du sujet principal de ce brief.
Maximum {max_keywords} mots-cles. Exemple de format : 'LangGraph Python agents StateGraph'

Brief : {user_input}""")
])

_FINAL_PROMPT = ChatPromptTemplate.from_messages([
    ("human", """\
Tu es un expert en ingenierie pedagogique et un redacteur senior de premier ordre. Ta mission est de rediger une fiche de reference claire, didactique et immediatement actionnable sur le sujet demande. Tonalite : inspire toi de celle utilisée par l'utilisateur dans {user_input}, et les réponses dans {questions_answers}.

## CONTEXTE ET DONNEES SOURCES (Tes seules verites factuelles)
- Brief original de l'utilisateur : {user_input}
- Analyse initiale du besoin : {analyse}
- CLARIFICATIONS DE L'UTILISATEUR (A integrer imperativement pour calibrer le niveau et les attentes) :
{questions_answers}
- INFORMATIONS ISSUES DU RECHERCHE WEB / RAG (Ta seule source autorisee pour les faits, chiffres ou specificites) :
{rag_result}

## DIRECTIVES CRITIQUES ANTI-HALLUCINATION
1. ANCRAGE STRICT AUX FAITS : Toutes les definitions, donnees, caracteristiques ou methodologies propres au sujet DOIVENT etre extraites ou validees par les "Informations issues du RAG". Si une information cruciale n'est pas presente, ne l'invente pas. Prefere rester factuel.
2. PAS D'IMPROVISATION DE CONTENU : Ne cree jamais de faux exemples magiques, de fausses statistiques ou des elements imaginaires pour simplifier ton explication. Tout exemple doit refleter la realite concrete du domaine aborde.
3. ADAPTATION AU PROFIL : Utilise les "Clarifications obtenues" pour aligner precisement la complexite, le vocabulaire et les exemples de la fiche avec le profil et les besoins reels formules par l'utilisateur.

## MISSION
Redige une fiche complete, structuree et immediatement utilisable au format Markdown.
Ne genere PAS de preambule ni de meta-commentaires (commence directement au titre #).

## STRUCTURE OBLIGATOIRE

# [Titre accrocheur et descriptif du sujet]

## Introduction
Contexte et enjeux en 3-4 phrases. Explique pourquoi ce sujet est crucial pour le profil cible.

## Concepts cles / Piliers majeurs
Sous forme d'UN SEUL tableau avec 4 colonnes : Concept | Definition | Analogie concrete | Exemple court. Sois synthetique (2-3 phrases max par case).

## Exemples pratiques et Applications concretes
Fournis au moins 2 exemples detailles, realistes, entierement differents de ceux esquisses dans la section Concepts cles. Si pertinent, inclus templates, scripts, ou cas d'ecole commentes.

## Exploration approfondie / Analyse detaillee
Decoupe en sous-sections avec des titres. Explore mecanismes, nuances, pieges, cas d'usage avances.

## Guide de mise en oeuvre / Plan d'action pas a pas
Etapes numerotees, precises et chronologiques. Chaque etape sur SA PROPRE LIGNE.

## Points a retenir
5 a 7 points, chaque point sur SA PROPRE LIGNE, commencant par `-` ou `*`.

## Pour aller plus loin
2-3 pistes d'approfondissement reelles, lectures, outils ou concepts connexes.

## Mot de fin
Message d'encouragement personnalise et cible pour l'utilisateur.

## CONTRAINTES DE REDACTION SEVERES
- Utilise des TABLEAUX des que possible (notamment Concepts cles, comparaisons, mise en oeuvre).
- Sois SYNTHETIQUE : phrases courtes. Chaque phrase doit apporter une valeur concrete.
- Les sous-sections doivent utiliser des titres Markdown, jamais du texte suivi de `:`.
- Interdiction absolue de meubler avec du texte generique.
 
## REGLES MARKDOWN STRICTES — OBLIGATOIRES
- CODE INLINE : n'utilise JAMAIS les backticks simples (`) pour entourer du texte ordinaire, 
  des phrases ou des items de liste. Les backticks simples sont UNIQUEMENT pour du code 
  (`variable`, `function()`, `SELECT *`). 
  INTERDIT : `- Mon point à retenir.`
  CORRECT  : - Mon point à retenir.
- LISTES : chaque item DOIT etre sur SA PROPRE LIGNE, commence par `- ` ou `1. `.
  INTERDIT : "Intro : - item A - item B" sur une seule ligne.
  CORRECT :
  Intro :
  - item A
  - item B
- LISTES NUMEROTEES : numeroter en continu (1, 2, 3, 4…). Ne jamais reprendre a 1 au milieu.
- SECTION "Points a retenir" : chaque point DOIT commencer par `- ` ou `* `.
  INTERDIT : une phrase seule sur sa ligne sans tiret.
  CORRECT : `- Les cycles iteratifs permettent de livrer plus rapidement.`
- SEPARATEURS : utiliser `---` seul sur sa ligne pour les separateurs horizontaux.""")
])


def call_model(state: BriefState, llm):
    """Analyze the brief with the LLM and determine if clarifications are needed."""
    user_input = state["input"]
    if len(user_input) > MAX_INPUT_LENGTH:
        return {"analyse": f"Erreur : le brief dépasse la limite de {MAX_INPUT_LENGTH} caractères."}
    history_plain = ""

    for msg in state["questions_answers"]:
        history_plain += f"{msg['q']} {msg['r']} \n"

    messages = _ANALYSIS_PROMPT.format_messages(
        user_input=user_input, history_plain=history_plain
    )
    print("Analyse du brief par l'IA...")
    try:
        response = llm.invoke(messages)
        return {"analyse": response.content}
    except Exception as e:
        print(f"   Erreur LLM : {e}")
        return {"analyse": f"Erreur lors de l'analyse : {e}"}


def ask(state: BriefState, llm):
    """Pause the graph via interrupt to ask the user a clarification question."""
    try:
        messages = _QUESTION_PROMPT.format_messages(analyse=state["analyse"], user_input=state["input"])
        question = llm.invoke(messages)
    except Exception as e:
        print(f"   Erreur LLM lors de la question : {e}")
        return {"questions_answers": [QA(q=f"Erreur : {e}", r="")]}

    approved = interrupt(question)
    return {"questions_answers": [QA(q=question.content, r=approved)]}


def retrieve(state: BriefState, llm):
    """Extract keywords, search the web with Tavily, and run RAG retrieval."""
    try:
        messages = _KEYWORD_PROMPT.format_messages(
            user_input=state["input"], max_keywords=MAX_KEYWORDS
        )
        print("Extraction des mots-cles...")
        query_response = llm.invoke(messages)
        print(f"   Mots-cles : {query_response.content}")
    except Exception as e:
        print(f"   Erreur extraction mots-cles : {e}")
        return {"rag_result": f"Erreur extraction mots-cles : {e}", "sources": []}

    print("Recherche web via Tavily...")
    try:
        tavily_tool = TavilySearch(max_results=TAVILY_MAX_RESULTS)
        results = tavily_tool.invoke(query_response.content[:TAVILY_INPUT_LIMIT])
        urls = [r["url"] for r in results["results"]]
        print(f"   {len(urls)} URL(s) trouvee(s)")
    except Exception as e:
        print(f"   Erreur recherche web : {e}")
        return {"rag_result": f"Erreur recherche web : {e}", "sources": []}

    rag_result = build_retriever(urls, state["input"])

    return {
        "rag_result": rag_result,
        "sources": urls,
    }


def generate_final_data(state: BriefState, llm):
    """Generate the final markdown fiche using the LLM with all gathered context."""
    print("Redaction de la fiche pedagogique par l'IA...")
    messages = _FINAL_PROMPT.format_messages(
        user_input=state["input"],
        analyse=state["analyse"],
        questions_answers=state["questions_answers"],
        rag_result=state["rag_result"],
    )
    try:
        response = llm.invoke(messages)
        return {"final_data": response.content}
    except Exception as e:
        print(f"   Erreur LLM lors de la generation : {e}")
        return {"final_data": f"# Erreur lors de la generation\n\nImpossible de generer la fiche : {e}"}


def _cleanup_output_dir(output_dir: str, max_files: int):
    """Remove oldest files in output_dir when count exceeds max_files."""
    try:
        files = sorted(
            [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".html")],
            key=os.path.getmtime,
        )
        while len(files) > max_files:
            os.remove(files.pop(0))
    except Exception:
        pass


def create_html(state: BriefState):
    """Convert the markdown fiche to HTML and write it to the output directory."""
    print("Generation du fichier HTML...")
    brief_initial = state.get("input", "N/A")
    history = state.get("questions_answers", [])
    raw_markdown = state.get("final_data", "")

    sources = state.get("sources", [])

    body_content_html = markdown_to_html(raw_markdown)

    final_html_output = render_dashboard_template(
        brief_initial=brief_initial,
        history=history,
        sources=sources,
        body_content=body_content_html
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = "output"
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{output_dir}/dashboard_{timestamp}.html"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_html_output)

        _cleanup_output_dir(output_dir, MAX_OUTPUT_FILES)

        return {"result_path": filename}
    except Exception as e:
        print(f"   Erreur ecriture fichier : {e}")
        return {"result_path": f"Erreur : {e}"}
