import streamlit as st
from utils.auth_manager import check_authentication, logout
from utils.supabase_manager import init_supabase
import webbrowser
from config.settings import URLS
from sections.onboarding import render_onboarding

st.set_page_config(
    page_title="SmartLegal - Sistema Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    # Inicialização do Supabase
    supabase = init_supabase()
    
    # Sidebar
    with st.sidebar:
        # Logo no topo
        st.image("logo.png", width=200)
        
        # Seção Smart Legal
        st.title("Smart Legal")
        if st.button("Home", use_container_width=True):
            st.session_state.page = "home"
        if st.button("Onboarding", use_container_width=True):
            st.session_state.page = "onboarding"
        
        # Criar espaço para empurrar o logout para baixo
        st.markdown("""
            <style>
                div[data-testid="stVerticalBlock"] div[style*="flex-direction: column;"] div[data-testid="stVerticalBlock"] {
                    gap: 0rem;
                }
                div[data-testid="stSidebarUserContent"] {
                    height: calc(100vh - 100px);
                    display: flex;
                    flex-direction: column;
                }
                .logout-container {
                    margin-top: auto;
                    padding-bottom: 1rem;
                }
                [data-testid="stImage"] {
                    margin-bottom: 1rem;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Container para logout e informações do usuário
        with st.container():
            st.markdown('<div class="logout-container">', unsafe_allow_html=True)
            if st.session_state.get('authenticated'):
                st.markdown("---")
                st.write("Usuário:", st.session_state.user.email)
                if st.button("Logout", use_container_width=True):
                    logout()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Verificação de autenticação
    if not check_authentication(supabase):
        st.warning("Por favor, faça login para continuar.")
        return
    
    # Renderizar página selecionada
    if not hasattr(st.session_state, 'page'):
        st.session_state.page = "home"
        
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "onboarding":
        render_onboarding()

def render_home():
    # Conteúdo principal - Menu
    st.title("Menu Principal")
    
    # Links Rápidos
    st.header("Links Rápidos")
    
    # Primeira linha de botões
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("Clientes Smart Legal", 
                      URLS["CLIENTES_SMARTLEGAL"],
                      use_container_width=True)
    with col2:
        st.link_button("Processos Em Andamento", 
                      URLS["PROCESSOS_ANDAMENTO"],
                      use_container_width=True)
    
    # Segunda linha de botões
    col3, col4 = st.columns(2)
    with col3:
        st.link_button("Leads Ads", 
                      URLS["LEADS_ADS"],
                      use_container_width=True)
    with col4:
        st.link_button("CRM RD Station", 
                      URLS["CRM_RD"],
                      use_container_width=True)
    
    # Terceira linha com um botão centralizado
    col5, _ = st.columns(2)
    with col5:
        st.link_button("Drive Gmail", 
                      URLS["DRIVE_GMAIL"],
                      use_container_width=True)
    
    # Seções existentes
    st.markdown("---")


if __name__ == "__main__":
    main() 