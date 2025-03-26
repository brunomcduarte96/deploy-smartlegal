from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY
from typing import Dict, Any, List, Optional
import streamlit as st
import logging
from datetime import datetime

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
        """Busca todos os casos de um cliente específico"""
        try:
            response = self.supabase.table('casos')\
                .select('id, nome_cliente, caso, assunto_caso, responsavel_comercial, pasta_caso_id, pasta_caso_url, created_at, chave_caso')\
                .eq('cliente_id', client_id)\
                .order('chave_caso', desc=True)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar casos do cliente: {str(e)}")
            return []

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

    def save_facts_for_training(self, caso: str, input_text: str, output_text: str):
        """Salva os fatos gerados para treinamento"""
        try:
            data = {
                'caso': caso,
                'input': input_text,
                'output': output_text,
                'created_at': datetime.now().isoformat()
            }
            
            response = self.supabase.table('fatosGPT').insert(data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao salvar fatos para treinamento: {str(e)}")
            raise Exception(f"Erro ao salvar para treinamento: {str(e)}")

    def get_all_jurisprudencias(self):
        """Busca todas as jurisprudências do banco de dados"""
        try:
            print("Tentando buscar jurisprudências...")  # Debug
            response = self.supabase.table('jurisprudenciaAereo').select('id, nome, texto, secao, "Tribunal", created_at').order('created_at', desc=True).execute()
            
            if not response:
                print("Resposta vazia do Supabase")  # Debug
                return []
                
            print(f"Dados recebidos: {response.data}")  # Debug
            
            if not response.data:
                print("response.data está vazio")  # Debug
                return []
                
            return response.data
            
        except Exception as e:
            print(f"Erro detalhado ao buscar jurisprudências: {str(e)}")  # Debug
            logger.error(f"Erro ao buscar jurisprudências: {str(e)}")
            raise e

    def add_jurisprudencia(self, jurisprudencia_data):
        """Adiciona uma nova jurisprudência ao banco de dados
        
        Args:
            jurisprudencia_data: Dicionário contendo os dados da jurisprudência
        """
        try:
            # Garantir que o campo Tribunal está presente (com T maiúsculo)
            if 'Tribunal' not in jurisprudencia_data:
                jurisprudencia_data['Tribunal'] = ''  # ou outro valor padrão
            
            response = self.supabase.table('jurisprudenciaAereo').insert(jurisprudencia_data).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao adicionar jurisprudência: {str(e)}")
            raise e

    def update_jurisprudencia(self, jurisprudencia_id, data):
        """Atualiza uma jurisprudência no banco de dados
        
        Args:
            jurisprudencia_id: ID da jurisprudência a ser atualizada
            data: Dicionário contendo os campos a serem atualizados
        """
        try:
            response = self.supabase.table('jurisprudenciaAereo').update(data).eq('id', jurisprudencia_id).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao atualizar jurisprudência: {str(e)}")
            raise e

    def delete_jurisprudencia(self, jurisprudencia_id):
        """Deleta uma jurisprudência do banco de dados
        
        Args:
            jurisprudencia_id: ID da jurisprudência a ser deletada
        """
        try:
            response = self.supabase.table('jurisprudenciaAereo').delete().eq('id', jurisprudencia_id).execute()
            return response.data
        except Exception as e:
            print(f"Erro ao deletar jurisprudência: {str(e)}")
            raise e

    def get_jurisprudencias_aereo(self):
        """Busca todas as jurisprudências da tabela jurisprudenciaAereo"""
        try:
            response = self.supabase.table('jurisprudenciaAereo').select('*').execute()
            return response.data
        except Exception as e:
            logger.error(f"Erro ao buscar jurisprudências: {str(e)}")
            raise Exception(f"Erro ao buscar jurisprudências: {str(e)}")

    def get_client_by_cpf(self, cpf):
        """Busca um cliente pelo CPF"""
        try:
            response = self.supabase.table('clientes').select('*').eq('cpf', cpf).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar cliente por CPF: {str(e)}")
            return None

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