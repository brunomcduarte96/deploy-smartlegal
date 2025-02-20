import streamlit as st
from typing import Optional
from supabase import Client, create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

def init_auth_state():
    """Inicializa o estado de autenticação no Streamlit"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'username' not in st.session_state:
        st.session_state.username = None

def init_supabase():
    """Inicializa o cliente Supabase"""
    try:
        if not st.secrets.get("SUPABASE_URL"):
            raise Exception("SUPABASE_URL não encontrada nas secrets")
        if not st.secrets.get("SUPABASE_KEY"):
            raise Exception("SUPABASE_KEY não encontrada nas secrets")
            
        return create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
    except Exception as e:
        st.error(f"Erro ao inicializar Supabase: {str(e)}")
        st.stop()

def login_form(supabase: Client) -> bool:
    """Renderiza o formulário de login e processa a autenticação"""
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = response.user
                st.session_state.authenticated = True
                return True
            except Exception as e:
                st.error("Erro ao fazer login. Verifique suas credenciais.")
                return False
    return False

def check_authentication():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        col1, col2 = st.columns([3, 2])
        with col1:
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            if st.button("Login"):
                try:
                    supabase = init_supabase()
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    st.session_state.authenticated = True
                    st.session_state.user = response.user
                    st.session_state.username = email.split('@')[0]  # Nome do usuário sem domínio
                    st.session_state.email = email  # Salvando o email completo
                    st.rerun()
                except Exception as e:
                    st.error("Erro no login. Verifique suas credenciais.")
                    return False
        return False
    return True

def logout():
    """Realiza o logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.user = None 

def handle_logout():
    """Faz logout do usuário"""
    if st.session_state.get('authenticated'):
        # Limpa todas as variáveis de sessão
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinicializa variáveis essenciais
        st.session_state.authenticated = False
        st.session_state.current_page = "home" 