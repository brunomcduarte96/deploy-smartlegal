from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from typing import Dict, Any, List, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

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
        """Insere dados na tabela especificada"""
        try:
            # Log dos dados que estão sendo inseridos
            logger.info(f"Tentando inserir dados na tabela {table}: {data}")
            
            # Verifica se é a tabela de clientes
            if table == 'clientes':
                # Verifica se o email já existe
                if self.check_email_exists(data['email']):
                    raise Exception("Email já cadastrado no sistema")
                
                # Verifica campos obrigatórios para clientes
                required_fields = ['nome_completo', 'email', 'cpf']
                for field in required_fields:
                    if not data.get(field):
                        raise Exception(f"Campo obrigatório não preenchido: {field}")
            
            # Verifica se é a tabela de casos
            elif table == 'casos':
                # Verifica campos obrigatórios para casos
                required_fields = ['cliente_id', 'nome_cliente', 'caso', 'assunto_caso', 'responsavel_comercial']
                for field in required_fields:
                    if not data.get(field):
                        raise Exception(f"Campo obrigatório não preenchido: {field}")
            
            # Tenta inserir os dados
            try:
                response = self.supabase.table(table)\
                    .insert(data)\
                    .execute()
                
                if not response.data or len(response.data) == 0:
                    raise Exception("Nenhum dado retornado após inserção")
                    
                logger.info(f"Dados inseridos com sucesso na tabela {table}")
                return response.data[0]
                
            except Exception as e:
                # Tenta obter mais detalhes do erro
                error_details = str(e)
                if hasattr(e, 'code'):
                    error_details += f" (Code: {e.code})"
                if hasattr(e, 'details'):
                    error_details += f" (Details: {e.details})"
                    
                logger.error(f"Erro na inserção no Supabase: {error_details}")
                raise Exception(f"Erro na inserção: {error_details}")
                
        except Exception as e:
            logger.error(f"Erro ao inserir dados na tabela {table}: {str(e)}")
            logger.error(f"Dados que tentaram ser inseridos: {data}")
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

    def check_table_exists(self, table: str) -> bool:
        """Verifica se a tabela existe"""
        try:
            response = self.supabase.table(table).select('count').limit(1).execute()
            return True
        except Exception:
            return False

    def get_all_clients(self):
        """Fetch all clients from the database"""
        try:
            response = self.supabase.table('clientes').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching clients: {str(e)}")
            raise e

    def update_client(self, client_id, data):
        """Update a client in the database
        
        Args:
            client_id: The ID of the client to update
            data: Dictionary containing the fields to update
        """
        try:
            response = self.supabase.table('clientes').update(data).eq('id', client_id).execute()
            return response.data
        except Exception as e:
            print(f"Error updating client: {str(e)}")
            raise e

    def delete_client(self, client_id):
        """Delete a client from the database
        
        Args:
            client_id: The ID of the client to delete
        """
        try:
            response = self.supabase.table('clientes').delete().eq('id', client_id).execute()
            return response.data
        except Exception as e:
            print(f"Error deleting client: {str(e)}")
            raise e

    def get_client_cases(self, client_id):
        """Get all cases associated with a client
        
        Args:
            client_id: The ID of the client
            
        Returns:
            List of cases associated with the client
        """
        try:
            response = self.supabase.table('casos').select('*').eq('cliente_id', client_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching client cases: {str(e)}")
            raise e

    def get_all_companies(self):
        """Fetch all airline companies from the database"""
        try:
            response = self.supabase.table('companhiasAereas').select('*').execute()
            return response.data
        except Exception as e:
            print(f"Error fetching companies: {str(e)}")
            raise e

    def add_company(self, company_data):
        """Add a new airline company to the database
        
        Args:
            company_data: Dictionary containing the company data
        """
        try:
            response = self.supabase.table('companhiasAereas').insert(company_data).execute()
            return response.data
        except Exception as e:
            print(f"Error adding company: {str(e)}")
            raise e

    def update_company(self, company_id, data):
        """Update an airline company in the database
        
        Args:
            company_id: The ID of the company to update
            data: Dictionary containing the fields to update
        """
        try:
            response = self.supabase.table('companhiasAereas').update(data).eq('id', company_id).execute()
            return response.data
        except Exception as e:
            print(f"Error updating company: {str(e)}")
            raise e

    def delete_company(self, company_id):
        """Delete an airline company from the database
        
        Args:
            company_id: The ID of the company to delete
        """
        try:
            response = self.supabase.table('companhiasAereas').delete().eq('id', company_id).execute()
            return response.data
        except Exception as e:
            print(f"Error deleting company: {str(e)}")
            raise e

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