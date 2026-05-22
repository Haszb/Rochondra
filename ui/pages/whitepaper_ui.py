# ui/pages/whitepaper_ui.py
import streamlit as st
import requests

# URL de ton endpoint FastAPI local
API_URL = "http://127.0.0.1:8000/api/whitepaper/extract"

st.title("Interface d'extraction (via API)")
extract_images = st.toggle("Activer l'analyse d'images", value=True)
uploaded_file = st.file_uploader("Fichier PDF", type=["pdf"])

if uploaded_file and st.button("Lancer l'extraction"):
    with st.spinner("Requête en cours de traitement par le serveur FastAPI..."):
        
        # 1. On prépare le fichier binaire pour l'envoi HTTP
        files = {
            "file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")
        }
        
        # 2. On prépare les données du formulaire
        data = {
            "extract_images": str(extract_images).lower() # Convertit True/False en "true"/"false"
        }
        
        try:
            # 3. Envoi de la requête POST à FastAPI
            response = requests.post(API_URL, files=files, data=data)
            
            # 4. Traitement de la réponse du serveur
            if response.status_code == 200:
                result_json = response.json()
                markdown_result = result_json.get("markdown_content", "")
                
                st.success("Extraction réussie !")
                st.text_area("Résultat", markdown_result, height=400)
            else:
                st.error(f"Erreur du serveur ({response.status_code}) : {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("Impossible de contacter le serveur FastAPI. Vérifie qu'il est bien lancé sur le port 8000.")