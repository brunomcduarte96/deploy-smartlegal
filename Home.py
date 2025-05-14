import streamlit as st
from sections.onboarding import render_onboarding
from sections.atraso_voo import render_atraso_voo
from sections.clientes import render_clientes
from sections.jurisprudencias import render_jurisprudencias
from sections.empresas import render_empresas
from utils.auth_manager import check_authentication, handle_logout
import os

def render_sidebar():
    """Renderiza a barra lateral com a estrutura definida"""
    # Logo
    logo_path = os.path.join("assets", "logo.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=200)
    
    st.sidebar.divider()  # Separador
    
    # Botão Home
    if st.sidebar.button("Home", use_container_width=True):
        st.session_state.current_page = "home"
        st.rerun()
        
    st.sidebar.divider()  # Separador
    
    # Seção Comercial
    st.sidebar.markdown("#### Comercial")
    if st.sidebar.button("Onboarding", use_container_width=True):
        st.session_state.current_page = "onboarding"
        st.rerun()
    
    if st.sidebar.button("Clientes", use_container_width=True):
        st.session_state.current_page = "clientes"
        st.rerun()
    
    if st.sidebar.button("Enviar Email", use_container_width=True):
        st.session_state.current_page = "gerar_documentos"
        st.rerun()
        
    st.sidebar.divider()  # Separador
    
    # Seção Jurídico
    st.sidebar.markdown("#### Jurídico")
    if st.sidebar.button("Atraso / Cancelamento de Voo", use_container_width=True):
        st.session_state.current_page = "atraso_voo"
        st.rerun()
    
    if st.sidebar.button("Bagagem Danificada", use_container_width=True):
        st.session_state.current_page = "bagagem_danificada"
        st.rerun()
    
    st.sidebar.divider()  # Separador
    
    # Seção Banco de Dados
    st.sidebar.markdown("#### Banco de Dados")
    if st.sidebar.button("Empresas", use_container_width=True):
        st.session_state.current_page = "empresas"
        st.rerun()
    
    if st.sidebar.button("Jurisprudências", use_container_width=True):
        st.session_state.current_page = "jurisprudencias"
        st.rerun()
    
    st.sidebar.divider()  # Separador
    
    # Seção do Usuário
    email = st.session_state.get('email', '')
    st.sidebar.markdown("#### Usuário")
    st.sidebar.text(email)
    if st.sidebar.button("Logout", use_container_width=True):
        handle_logout()
        st.rerun()

def render_home():
    """Renderiza a página inicial"""
    st.title("Smart Legal")
    st.write("Bem-vindo ao sistema de gestão Smart Legal")

def main():
    # Verifica autenticação
    if not check_authentication():
        st.stop()
    
    # Inicializa o estado da página se necessário
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    # Renderiza a barra lateral
    render_sidebar()
    
    # Renderiza a página atual
    if st.session_state.current_page == "home":
        render_home()
    elif st.session_state.current_page == "onboarding":
        render_onboarding()
    elif st.session_state.current_page == "atraso_voo":
        render_atraso_voo()
    elif st.session_state.current_page == "bagagem_danificada":
        st.info("Página em desenvolvimento")  # Placeholder até implementarmos
    elif st.session_state.current_page == "clientes":
        render_clientes()
    elif st.session_state.current_page == "jurisprudencias":
        render_jurisprudencias()
    elif st.session_state.current_page == "empresas":
        render_empresas()
    elif st.session_state.current_page == "gerar_documentos":
        from sections.gerar_documentos import render_gerar_documentos
        render_gerar_documentos()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Smart Legal",
        page_icon="⚖️",
        layout="wide"
    )
    main() 