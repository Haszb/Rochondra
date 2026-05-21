# ui/app.py
import streamlit as st
import sys
from pathlib import Path
import tempfile

# Récupère la racine du projet (deux niveaux au-dessus de app/streamlit/app.py)
root_path = Path(__file__).resolve().parents[2]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Importation du MEME module commun
from Modules.Whitepaper.extractor import pdf_to_semantic_markdown




st.title("Interface d'extraction")
extract_images = st.toggle("Activer l'analyse d'images", value=True)
uploaded_file = st.file_uploader("Fichier PDF", type=["pdf"])

if uploaded_file and st.button("Lancer l'extraction"):
    with st.spinner("Traitement..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            temp_pdf_path = temp_dir_path / uploaded_file.name
            temp_md_output = temp_dir_path / "output.md"
            temp_img_dir = temp_dir_path / "images_tmp"
            
            temp_pdf_path.write_bytes(uploaded_file.getvalue())
            
            # Appel de la logique commune
            markdown_result = pdf_to_semantic_markdown(
                pdf_path=str(temp_pdf_path),
                output_md=str(temp_md_output),
                img_dir=str(temp_img_dir),
                extract_images=extract_images
            )
            
            st.success("Terminé !")
            st.text_area("Résultat", markdown_result, height=400)