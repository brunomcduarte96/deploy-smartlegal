import streamlit as st
from typing import Optional
from supabase import Client

def init_auth_state():
    """Inicializa o estado de autenticação no Streamlit"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None

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

def check_authentication(supabase: Client) -> bool:
    """Verifica se o usuário está autenticado"""
    init_auth_state()
    
    if st.session_state.authenticated:
        return True
    
    return login_form(supabase)

def logout():
    """Realiza o logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.user = None 