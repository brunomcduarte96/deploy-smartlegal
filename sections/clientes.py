import streamlit as st
from utils.supabase_manager import SupabaseManager
from utils.error_handler import handle_error
import pandas as pd

def validate_cpf(cpf):
    """Validates CPF format"""
    # Remove non-numeric characters
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    return len(cpf) == 11

def validate_email(email):
    """Simple email validation"""
    return '@' in str(email) and '.' in str(email).split('@')[1]

def process_client_update(edited_rows, original_rows):
    """Process updates to client data"""
    supabase = SupabaseManager()
    
    try:
        for index, changes in edited_rows.items():
            if not changes:  # Skip if no changes
                continue
                
            original_row = original_rows.iloc[index]
            client_id = original_row['id']
            
            st.write(f"Processando alterações para cliente {client_id}: {changes}")  # Debug message
            
            # Validate fields if they were changed
            if 'cpf' in changes and not validate_cpf(changes['cpf']):
                st.error(f"CPF inválido na linha {index + 1}")
                continue
                
            if 'email' in changes and not validate_email(changes['email']):
                st.error(f"Email inválido na linha {index + 1}")
                continue
            
            # Update the client in Supabase
            try:
                supabase.update_client(client_id, changes)
                st.success(f"Cliente {client_id} atualizado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar cliente {client_id}: {str(e)}")
        
    except Exception as e:
        handle_error("Erro ao atualizar dados do cliente", e)

def delete_client(client_id):
    """Delete a client from the database"""
    supabase = SupabaseManager()
    try:
        # Debug message
        st.write(f"Tentando excluir cliente {client_id}")
        
        # Verificar se o cliente tem casos
        casos = supabase.get_client_cases(client_id)
        if casos and len(casos) > 0:
            st.error(
                "Não é possível excluir este cliente pois existem casos associados a ele. "
                "Para excluir o cliente, primeiro exclua todos os casos relacionados."
            )
            return
        
        # Delete from database
        supabase.delete_client(client_id)
        
        # Clear session state
        st.session_state.pop('confirm_delete', None)
        st.session_state.show_delete_modal = False
        
        st.success("Cliente excluído com sucesso!")
        st.rerun()
        
    except Exception as e:
        if "violates foreign key constraint" in str(e):
            st.error(
                "Não é possível excluir este cliente pois existem casos associados a ele. "
                "Para excluir o cliente, primeiro exclua todos os casos relacionados."
            )
        else:
            st.error(f"Erro ao excluir cliente: {str(e)}")
            handle_error("Erro ao excluir cliente", e)

def render_clientes():
    """Render the clients page"""
    st.title("Gestão de Clientes")
    
    supabase = SupabaseManager()
    
    try:
        # Fetch clients data
        clients_data = supabase.get_all_clients()
        
        if not clients_data:
            st.info("Nenhum cliente cadastrado.")
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(clients_data)
        
        # Create a copy of original data for comparison
        original_df = df.copy()
        
        # Get visible columns (excluding 'id')
        visible_columns = [col for col in df.columns if col != 'id']
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_order=visible_columns,  # Only show these columns
            key="client_editor",
            on_change=lambda: st.session_state.update({'data_editor_changed': True})
        )
        
        # Process any edits
        if st.session_state.get('data_editor_changed', False):
            st.write("Detectada mudança na tabela")  # Debug message
            edited_rows = {}
            
            # Compare original and edited dataframes
            for idx, row in edited_df.iterrows():
                changes = {}
                original_row = original_df.iloc[idx]
                
                # Check each column for changes
                for col in visible_columns:
                    if row[col] != original_row[col]:
                        changes[col] = row[col]
                
                if changes:  # If there are changes for this row
                    edited_rows[idx] = changes
            
            if edited_rows:
                st.write(f"Mudanças detectadas: {edited_rows}")  # Debug message
                process_client_update(edited_rows, original_df)
                st.session_state.data_editor_changed = False
                st.rerun()
            
    except Exception as e:
        st.write(f"Erro detalhado: {str(e)}")  # More detailed error message
        handle_error("Erro ao carregar dados dos clientes", e) 