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
        if st.button("Clientes Smart Legal", use_container_width=True):
            webbrowser.open_new_tab(URLS["CLIENTES_SMARTLEGAL"])
    with col2:
        if st.button("Processos Em Andamento", use_container_width=True):
            webbrowser.open_new_tab(URLS["PROCESSOS_ANDAMENTO"])
    
    # Segunda linha de botões
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Leads Ads", use_container_width=True):
            webbrowser.open_new_tab(URLS["LEADS_ADS"])
    with col4:
        if st.button("CRM RD Station", use_container_width=True):
            webbrowser.open_new_tab(URLS["CRM_RD"])
    
    # Terceira linha com um botão centralizado
    col5, _ = st.columns(2)
    with col5:
        if st.button("Drive Gmail", use_container_width=True):
            webbrowser.open_new_tab(URLS["DRIVE_GMAIL"])
    
    # Seções existentes
    st.markdown("---")
    st.header("Funcionalidades do Sistema")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Onboarding")
        st.markdown("""
        - Cadastro de novos clientes
        - Geração automática de procuração
        - Upload e organização de documentos
        - Armazenamento no Google Drive
        """)
    
    with col2:
        st.subheader("Módulo Aéreo")
        st.markdown("""
        #### Atraso / Cancelamento de Voo
        - Geração de petições iniciais
        - Cálculo de indenizações
        - Jurisprudência específica
        
        #### Extravio de Bagagem
        - Petições automatizadas
        - Cálculo de danos materiais
        - Precedentes judiciais
        """)

if __name__ == "__main__":
    main() 