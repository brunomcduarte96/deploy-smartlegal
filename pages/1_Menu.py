import streamlit as st
from config.settings import URLS
from utils.auth_manager import check_authentication
from utils.supabase_manager import init_supabase

def create_menu_button(text: str, url: str):
    """Cria um botão estilizado para o menu"""
    st.markdown(
        f"""
        <a href="{url}" target="_blank" style="text-decoration: none;">
            <div style="
                background-color: #0066cc;
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin: 10px 0px;
                font-size: 18px;
                cursor: pointer;
                transition: background-color 0.3s;">
                {text}
            </div>
        </a>
        """,
        unsafe_allow_html=True
    )

def main():
    # Verificação de autenticação
    supabase = init_supabase()
    if not check_authentication(supabase):
        return

    st.title("Menu Principal")
    
    # Descrição da página
    st.write("""
    Bem-vindo ao menu principal do sistema SmartLegal.
    Selecione uma das opções abaixo para acessar as diferentes áreas do sistema.
    """)
    
    # Container para os botões
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            create_menu_button("Clientes SmartLegal", URLS["CLIENTES_SMARTLEGAL"])
            create_menu_button("Leads Ads", URLS["LEADS_ADS"])
            create_menu_button("Drive Gmail", URLS["DRIVE_GMAIL"])
            
        with col2:
            create_menu_button("Processos em Andamento", URLS["PROCESSOS_ANDAMENTO"])
            create_menu_button("CRM RD Station", URLS["CRM_RD"])
    
    # Informações adicionais
    st.markdown("---")
    st.markdown("""
    ### Precisa de ajuda?
    Em caso de dúvidas ou problemas, entre em contato com o suporte técnico.
    """)

if __name__ == "__main__":
    main() 