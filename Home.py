import streamlit as st
from utils.auth_manager import check_authentication
from utils.supabase_manager import init_supabase

st.set_page_config(
    page_title="SmartLegal - Sistema Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Inicialização do Supabase
    supabase = init_supabase()
    
    # Verificação de autenticação
    if not check_authentication(supabase):
        st.warning("Por favor, faça login para continuar.")
        return
    
    st.title("SmartLegal - Sistema Jurídico")
    st.write("""
    Bem-vindo ao sistema jurídico da SmartLegal.
    
    Use o menu lateral para navegar entre as diferentes funcionalidades do sistema.
    """)
    
    # Informações adicionais
    with st.sidebar:
        st.image("logo.png", width=200)  # Adicione o logo da empresa
        st.markdown("---")

if __name__ == "__main__":
    main() 