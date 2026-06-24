"""Entry point for the ChatBotLangGraph brief analysis application."""
import uuid

from agentbrief.graph import graph
from langgraph.types import Command

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

print("""
╔══════════════════════════════════════════════════════════╗
║           Analyseur de Brief - © Umberto Emonds          ║
╚══════════════════════════════════════════════════════════╝

  Décris ton brief (sujet). Nous l'analyserons pour toi et te 
  poserons des questions de clarification si nécessaire.
  Une fiche HTML pédagogique et structurée sera générée à l'issue de cette séance.
""")

user_brief = input("  À toi de jouer : ")
print("\n  ⏳ Analyse en cours...\n")

result = graph.invoke(
    {"input": user_brief, "questions_answers": []},
    config=config
)

question_count = 0

while "__interrupt__" in result:
    question_count += 1
    interrupt_value = result["__interrupt__"][0].value

    print(f"\n  ❓ Question {question_count} :")
    print(f"  {interrupt_value.content}\n")
    user_response = input("  Votre réponse : ")
    print("\n  ⏳ Traitement en cours...\n")

    result = graph.invoke(
        Command(resume=user_response),
        config=config
    )

print("\n" + "─" * 60)
print(f"Fiche HTML générée avec succès 📄 ({result['result_path']})")
print("─" * 60 + "\n")
