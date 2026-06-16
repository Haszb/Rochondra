import streamlit as st
import requests

from core_shared.config import API_URL

API_WHITEPAPER_URL = f"{API_URL}/whitepaper"

# Session HTTP persistante — maintient le cookie Starlette entre les appels
if "http_session" not in st.session_state:
    st.session_state["http_session"] = requests.Session()

http = st.session_state["http_session"]  # ← alias court

# ---------------------------------------------------------------------------
# Section 1 — Extraction
# ---------------------------------------------------------------------------
st.header("1. Extraction du PDF")

extract_images = st.toggle("Activer l'analyse d'images", value=True)
save_markdown  = st.toggle("Sauvegarder le Markdown", value=True)
project_name   = st.text_input("Nom du projet (optionnel)")
uploaded_file  = st.file_uploader("Fichier PDF", type=["pdf"])

if uploaded_file and st.button("Lancer l'extraction"):
    with st.spinner("Requête en cours de traitement par le serveur FastAPI..."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        data  = {
            "extract_images": str(extract_images).lower(),
            "save_markdown":  str(save_markdown).lower(),
            "project_name":   project_name,
        }
        try:
            response = http.post(f"{API_WHITEPAPER_URL}/extract", files=files, data=data)  # ← http
            if response.status_code == 200:
                result_json = response.json()
                st.session_state["doc_uuid"] = result_json.get("doc_uuid")
                st.success("Extraction réussie !")
                st.text_area("Résultat Markdown", result_json.get("markdown_content", ""), height=400)
            else:
                st.error(f"Erreur du serveur ({response.status_code}) : {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Impossible de contacter le serveur FastAPI. Vérifie qu'il est bien lancé sur le port 8000.")

# ---------------------------------------------------------------------------
# Section 2 — Analyse structurelle
# ---------------------------------------------------------------------------
st.divider()
st.header("2. Analyse structurelle")

doc_uuid = st.session_state.get("doc_uuid")

if doc_uuid:
    st.caption(f"Document en session : `{doc_uuid}`")
else:
    st.info("Aucun document en session — lancez d'abord une extraction.")

include_images_stats = st.toggle("Inclure les stats d'images", value=False)

if st.button("Lancer l'analyse structurelle", disabled=not doc_uuid):
    with st.spinner("Analyse en cours..."):
        try:
            response = http.post(  # ← http
                f"{API_WHITEPAPER_URL}/structural_analysis",
                data={"include_images_stats": str(include_images_stats).lower()},
            )
            if response.status_code == 200:
                result_json = response.json()
                st.success("Analyse structurelle réussie !")
                st.json(result_json.get("metrics", {}))
            else:
                st.error(f"Erreur du serveur ({response.status_code}) : {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("Impossible de contacter le serveur FastAPI. Vérifie qu'il est bien lancé sur le port 8000.")