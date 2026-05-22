# ui/app.py
import streamlit as st
import sys
from pathlib import Path

# Récupère la racine du projet (deux niveaux au-dessus de app/streamlit/app.py)
ROOT_GLOBAL = Path(__file__).resolve().parent.parent
if str(ROOT_GLOBAL) not in sys.path:
    sys.path.insert(0, str(ROOT_GLOBAL))

# Configuration de la page (doit être appelée une seule fois, ici !)
st.set_page_config(page_title="Rochondra Lab", layout="wide")

# Définition des pages disponibles
whitepaper_page = st.Page("pages/whitepaper_ui.py", title="Whitepaper Analyst", icon="📄")
# tokenomics_page = st.Page("pages/tokenomics_ui.py", title="Tokenomics Metrics", icon="📊")

# Initialisation de la navigation
pg = st.navigation([whitepaper_page])  # , tokenomics_page])
pg.run()

