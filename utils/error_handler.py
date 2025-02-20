class SmartLegalError(Exception):
    """Classe base para exceções customizadas"""
    pass

class DriveError(SmartLegalError):
    """Erros relacionados ao Google Drive"""
    pass

class DatabaseError(SmartLegalError):
    """Erros relacionados ao Supabase"""
    pass

def handle_error(error: Exception, show_user: bool = True):
    """Tratamento centralizado de erros"""
    import streamlit as st
    import logging
    
    error_map = {
        'AuthenticationError': 'Erro de autenticação. Por favor, faça login novamente.',
        'DriveError': 'Erro ao acessar o Google Drive. Tente novamente em alguns minutos.',
        'DatabaseError': 'Erro ao acessar o banco de dados. Tente novamente em alguns minutos.',
        'ValidationError': 'Dados inválidos. Verifique os campos e tente novamente.'
    }
    
    # Log do erro
    logging.error(f"Error: {str(error)}")
    
    # Mensagem para o usuário
    if show_user:
        error_type = error.__class__.__name__
        message = error_map.get(error_type, 'Ocorreu um erro. Por favor, tente novamente.')
        st.error(message) 