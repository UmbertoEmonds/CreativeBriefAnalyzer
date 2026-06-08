from langgraph.types import interrupt
from agentbrief.rag import build_retriever
from agentbrief.state import BriefState, QA
from langchain_tavily import TavilySearch
from datetime import datetime
import os

def call_model(state: BriefState, llm):
    """
        Analyze a creative brief using an LLM.

        Builds a prompt combining the original brief and any previous
        clarification history, then invokes the LLM. If the brief lacks
        essential information (target audience, format, objective), the LLM
        is instructed to begin its response with 'CLARIFICATION_NEEDED'.

        Args:
            state (BriefState): The current graph state, containing the
                original brief ('input') and clarification history
                ('questions_answers').
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'analyse' containing
            the LLM's analysis as a string.
    """
    user_input = state["input"]
    history_plain = ""

    for msg in state["questions_answers"]:
        history_plain += f"{msg['q']} {msg['r']} \n"

    response = llm.invoke(
        f"""
        Tu es un assistant qui analyse des briefs créatifs.
        Analyse ce brief : {user_input}
        
        Historique des clarifications : {history_plain}

        Si le brief manque d'informations essentielles (cible, format, objectif), commence ta réponse par CLARIFICATION_NEEDED.
        Sinon, fais directement une analyse complète.
        """
    )
    return {"analyse": response.content}


def ask(state: BriefState, llm):
    """
        Generate a clarification question and interrupt the graph for user input.

        Uses the current analysis to generate a targeted question via the LLM,
        then suspends graph execution using LangGraph's interrupt mechanism.
        Once the user provides an answer, the question/answer pair is stored
        in the state.

        Args:
            state (BriefState): The current graph state, containing the
                LLM's analysis ('analyse').
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'questions_answers'
                containing a list with a single QA entry.
    """
    question = llm.invoke(
        f" {state['analyse']}. A partir de ces informations, génère UNIQUEMENT une question qui sera renvoyée directement à l'utilisateur.")
    approved = interrupt(question)

    return {"questions_answers": [QA(q=question.content, r=approved)]}

def retrieve(state: BriefState, llm):
    query_response = llm.invoke(
        f"""Extrais UNIQUEMENT les mots-clés techniques du sujet principal de ce brief.
        Ignore le format de livrable (carte mentale, PDF, slides...).
        Maximum 5 mots-clés. Exemple de format : 'LangGraph Python agents StateGraph'

        Brief : {state['input']}"""
    )

    # Tavily input limit : 400
    tavily_tool = TavilySearch(max_results=10)

    results = tavily_tool.invoke(query_response.content[:400])
    urls = [r["url"] for r in results["results"]]

    rag_result = build_retriever(urls, state["input"])

    return {"rag_result": rag_result}

def generate_final_data(state: BriefState, llm):
    """
        Generate the final structured content for the PDF sheet.

        Combines all available state information (brief, analysis,
        clarifications, web research) into a comprehensive prompt and
        invokes the LLM to produce the final fiche content. The output
        includes key concepts, concrete examples, takeaways, and an
        encouraging message for the target audience.

        Args:
            state (BriefState): The current graph state containing 'input',
                'analyse', 'questions_answers', and 'web_result'.
            llm: A LangChain-compatible LLM instance.

        Returns:
            dict: A partial state update with the key 'final_data' containing the generated content as a string.
    """
    response = llm.invoke(
        f"""
        Tu es un expert pédagogique qui rédige des fiches de référence claires et actionnables.
        
        ## Contexte
        Brief original : {state['input']}
        Analyse du brief : {state['analyse']}
        Clarifications obtenues : {state['questions_answers']}
        Sources web consultées : {state['rag_result']}
        
        ## Mission
        Rédige une fiche complète, didactique et immédiatement utilisable au format Markdown.
        Le contenu doit être réel, précis et adapté au profil cible identifié dans le brief.
        Ne génère PAS de méta-commentaires sur la fiche — génère directement le contenu.
        
        ## Structure obligatoire
        
        # [Titre accrocheur et descriptif]
        
        ## Introduction
        Contexte et enjeux en 3-4 phrases. Pourquoi ce sujet est important pour le profil cible.
        
        ## Concepts clés
        Pour chaque concept : définition simple, analogie concrète, exemple d'usage.
        
        ## Exemples concrets
        Minimum 2 exemples détaillés et applicables immédiatement.
        Si pertinent, inclure des blocs de code avec syntaxe correcte.
        
        ## Exploration approfondie
        Description complète des mécanismes, nuances et cas d'usage avancés.
        
        ## Mise en œuvre — Guide pas à pas
        Étapes numérotées, précises et actionnables.
        Chaque étape doit être suffisamment détaillée pour être suivie sans ambiguïté.
        
        ## Points à retenir
        5 à 7 points essentiels en bullet points.
        
        ## Pour aller plus loin
        2-3 ressources ou pistes d'approfondissement.
        
        ## Mot de fin
        Message d'encouragement personnalisé pour le profil cible identifié.
        
        ## Contraintes de rédaction
        - Ton : adapté au profil cible identifié dans le brief et l'analyse
        - Utilise tout ce que Markdown permet : titres, bold, italic, code, tableaux, listes
        - Chaque section doit avoir du contenu substantiel — pas de remplissage
        - Les exemples de code doivent être corrects et fonctionnels
        """
    )

    return {"final_data": response.content}

def create_markdown(state: BriefState):
    content = state.get("final_data", "Aucun contenu généré.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/brief_{timestamp}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    return {"result_path": filename}