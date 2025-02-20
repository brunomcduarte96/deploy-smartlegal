from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from typing import Dict, Any, List, Optional
import streamlit as st

class SupabaseManager:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    def check_email_exists(self, email: str) -> bool:
        """Verifica se o email já existe no banco"""
        try:
            response = self.supabase.table('clientes')\
                .select('email')\
                .eq('email', email)\
                .execute()
            return len(response.data) > 0
        except Exception as e:
            raise Exception(f"Erro ao verificar email: {str(e)}")
    
    def insert_client_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insere dados do cliente na tabela especificada"""
        try:
            # Verifica se o email já existe
            if self.check_email_exists(data['email']):
                raise Exception("Email já cadastrado no sistema")
                
            response = self.supabase.table(table).insert(data).execute()
            return response.data[0]
        except Exception as e:
            raise Exception(f"Erro ao inserir dados: {str(e)}")
    
    def update_client_data(self, table: str, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza dados do cliente na tabela especificada"""
        try:
            response = self.supabase.table(table).update(data).eq('id', id).execute()
            return response.data[0]
        except Exception as e:
            raise Exception(f"Erro ao atualizar dados: {str(e)}")
    
    def get_client_data(self, table: str, id: int) -> Dict[str, Any]:
        """Recupera dados do cliente da tabela especificada"""
        try:
            response = self.supabase.table(table).select("*").eq('id', id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Erro ao recuperar dados: {str(e)}")
    
    def delete_client_data(self, table: str, id: int) -> bool:
        """Deleta dados do cliente da tabela especificada"""
        try:
            self.supabase.table(table).delete().eq('id', id).execute()
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar dados: {str(e)}")

    def search_clients(self, search_term: str = None, limit: int = 10):
        """
        Busca clientes por nome, email ou CPF
        
        Args:
            search_term: Termo para busca (nome, email ou CPF)
            limit: Número máximo de resultados
        
        Returns:
            Lista de clientes encontrados
        """
        try:
            query = self.supabase.table('clientes').select('*')
            
            if search_term:
                search_term = search_term.strip().lower()
                query = query.or_(
                    f"nome_completo.ilike.%{search_term}%,"
                    f"email.ilike.%{search_term}%,"
                    f"cpf.ilike.%{search_term}%"
                )
            
            response = query.limit(limit).execute()
            return response.data
        except Exception as e:
            raise Exception(f"Erro ao buscar clientes: {str(e)}")

    def get_client_by_name(self, nome_completo: str):
        """
        Busca cliente pelo nome completo exato
        
        Args:
            nome_completo: Nome completo do cliente
        
        Returns:
            Dados do cliente ou None se não encontrado
        """
        try:
            response = self.supabase.table('clientes')\
                .select('*')\
                .eq('nome_completo', nome_completo)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Erro ao buscar cliente por nome: {str(e)}")

    def search_clients_by_partial_name(self, partial_name: str, limit: int = 10):
        """
        Busca clientes por parte do nome
        
        Args:
            partial_name: Parte do nome para busca
            limit: Número máximo de resultados
        
        Returns:
            Lista de clientes encontrados
        """
        try:
            response = self.supabase.table('clientes')\
                .select('*')\
                .ilike('nome_completo', f'%{partial_name}%')\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            raise Exception(f"Erro ao buscar clientes por nome parcial: {str(e)}")

    def get_client_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Busca cliente pelo email
        
        Args:
            email: Email do cliente
        
        Returns:
            Dados do cliente ou None se não encontrado
        """
        try:
            response = self.supabase.table('clientes')\
                .select('*')\
                .eq('email', email)\
                .execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise Exception(f"Erro ao buscar cliente por email: {str(e)}")

def init_supabase() -> Client:
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