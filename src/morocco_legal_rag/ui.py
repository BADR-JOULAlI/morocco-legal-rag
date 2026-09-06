"""Industrial-style Gradio interface with an evidence rail."""

from __future__ import annotations

import os

import gradio as gr
import requests


CSS = """
:root { --signal: #FFB800; --ink: #F4F4F0; --muted: #A4A69F; --line: #33352F; }
.gradio-container { background: #0B0C0A !important; color: var(--ink) !important; font-family: "IBM Plex Mono", "JetBrains Mono", monospace !important; }
.legal-shell { border: 1px solid var(--line); padding: 20px; }
.legal-title { color: var(--signal); letter-spacing: -0.05em; font-size: clamp(34px, 7vw, 82px); line-height: .9; margin: 0 0 18px; }
.evidence-rail { border-left: 2px solid var(--signal); padding-left: 18px; min-height: 360px; }
button.primary { background: var(--signal) !important; color: #000 !important; border: 1px solid var(--signal) !important; border-radius: 0 !important; }
textarea, input, .wrap, .form { border-radius: 0 !important; box-shadow: none !important; }
.legal-warning { color: var(--muted); border-top: 1px solid var(--line); padding-top: 12px; }
"""


def query_api(question: str, language: str, top_k: int) -> tuple[str, str]:
    api_url = os.getenv("RAG_API_URL", "http://localhost:8000")
    response = requests.post(
        f"{api_url}/ask",
        json={"question": question, "language": language, "top_k": top_k},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    citations = payload.get("citations", [])
    evidence = "\n\n".join(
        f"### {item['title']}\nPage {item['page']} · score {item['score']:.4f}\n\n{item['excerpt']}\n\n{item.get('url', '')}"
        for item in citations
    ) or "Aucune source suffisamment pertinente."
    return payload["answer"], evidence


def create_ui() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="Morocco Legal RAG") as interface:
        gr.HTML('<div class="legal-shell"><h1 class="legal-title">MOROCCO<br>LEGAL RAG</h1><p>Recherche documentaire multilingue avec citations vérifiables.</p></div>')
        with gr.Row():
            with gr.Column(scale=3):
                question = gr.Textbox(label="Question", lines=5, placeholder="Posez une question sur les documents indexés…")
                language = gr.Radio([("Français", "fr"), ("العربية", "ar"), ("الدارجة", "darija")], value="fr", label="Langue de réponse")
                top_k = gr.Slider(1, 10, value=5, step=1, label="Nombre de passages")
                submit = gr.Button("Rechercher", variant="primary")
                answer = gr.Markdown(label="Réponse")
            with gr.Column(scale=2, elem_classes="evidence-rail"):
                sources = gr.Markdown("Aucune recherche effectuée.", label="Preuves et sources")
        gr.HTML('<p class="legal-warning">Information documentaire uniquement — ne constitue pas un avis juridique.</p>')
        submit.click(query_api, [question, language, top_k], [answer, sources])
    return interface


def run() -> None:
    create_ui().launch(server_name="0.0.0.0", server_port=7860)
