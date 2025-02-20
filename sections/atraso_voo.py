import streamlit as st
from utils.supabase_manager import SupabaseManager
from utils.google_manager import GoogleManager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def render_atraso_voo():
    st.title("Atraso / Cancelamento de Voo")
    
    # Inicialização dos gerenciadores
    supabase_manager = SupabaseManager()
    google_manager = GoogleManager()
    
    # Aqui vai o conteúdo da página
    st.write("Em desenvolvimento...") 