import streamlit as st
from utils.supabase_manager import SupabaseManager
from utils.error_handler import handle_error
import pandas as pd

def validate_cnpj(cnpj):
    """Validates CNPJ format"""
    # Remove non-numeric characters
    cnpj = ''.join(filter(str.isdigit, str(cnpj)))
    return len(cnpj) == 14

def process_company_update(edited_rows, original_rows):
    """Process updates to company data"""
    supabase = SupabaseManager()
    
    try:
        for index, changes in edited_rows.items():
            if not changes:  # Skip if no changes
                continue
                
            original_row = original_rows.iloc[index]
            company_id = original_row['id']
            
            # Validate fields if they were changed
            if 'cnpj' in changes and not validate_cnpj(changes['cnpj']):
                st.error(f"CNPJ inválido na linha {index + 1}")
                continue
            
            # Update the company in Supabase
            try:
                supabase.update_company(company_id, changes)
                st.success(f"Empresa atualizada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar empresa: {str(e)}")
        
    except Exception as e:
        handle_error("Erro ao atualizar dados da empresa", e)

def add_new_company():
    """Add a new airline company"""
    st.subheader("Adicionar Nova Empresa")
    
    with st.form("new_company_form"):
        nome = st.text_input("Nome da Empresa")
        cnpj = st.text_input("CNPJ")
        endereco = st.text_input("Endereço")
        
        submitted = st.form_submit_button("Adicionar")
        
        if submitted:
            if not nome or not cnpj:  # Endereço não é obrigatório
                st.error("Nome da Empresa e CNPJ são campos obrigatórios")
                return
                
            if not validate_cnpj(cnpj):
                st.error("CNPJ inválido")
                return
                
            try:
                supabase = SupabaseManager()
                new_company = {
                    'nome': nome,
                    'cnpj': cnpj,
                    'endereco': endereco
                }
                
                supabase.add_company(new_company)
                st.success("Empresa adicionada com sucesso!")
                st.rerun()
                
            except Exception as e:
                handle_error("Erro ao adicionar empresa", e)

def delete_company(company_id):
    """Delete a company from the database"""
    supabase = SupabaseManager()
    try:
        supabase.delete_company(company_id)
        st.success("Empresa excluída com sucesso!")
        st.rerun()
    except Exception as e:
        handle_error("Erro ao excluir empresa", e)

def render_empresas():
    """Render the empresas page"""
    st.title("Gestão de Empresas")
    
    # Add company button
    if st.button("+ Adicionar Nova Empresa"):
        st.session_state.show_add_company = True
        
    # Show add company form
    if st.session_state.get('show_add_company', False):
        add_new_company()
        st.divider()
    
    supabase = SupabaseManager()
    
    try:
        # Fetch companies data
        companies_data = supabase.get_all_companies()
        
        if not companies_data:
            st.info("Nenhuma empresa cadastrada.")
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(companies_data)
        
        # Add delete button column
        df['Ações'] = None
        
        # Create a copy of original data for comparison
        original_df = df.copy()
        
        # Get visible columns (excluding 'id')
        visible_columns = ['nome', 'cnpj', 'endereco']
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_order=visible_columns,
            key="company_editor",
            on_change=lambda: st.session_state.update({'data_editor_changed': True})
        )

        # Add delete buttons in a separate section
        st.write("### Ações")
        for idx, row in original_df.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['nome']}** - {row['cnpj']}")
            with col2:
                if st.button("Excluir", key=f"del_{row['id']}", type="primary"):
                    delete_company(row['id'])
        
        # Process any edits
        if st.session_state.get('data_editor_changed', False):
            edited_rows = {}
            
            # Handle delete actions and collect edits
            for idx, row in edited_df.iterrows():
                if row['Ações']:  # If delete button was clicked
                    company_id = original_df.iloc[idx]['id']
                    delete_company(company_id)
                else:
                    # Check for edits (existing logic)
                    changes = {}
                    original_row = original_df.iloc[idx]
                    for col in visible_columns:
                        if col != 'Ações' and row[col] != original_row[col]:
                            changes[col] = row[col]
                    
                    if changes:
                        edited_rows[idx] = changes
            
            if edited_rows:
                process_company_update(edited_rows, original_df)
                st.session_state.data_editor_changed = False
                st.rerun()
            
    except Exception as e:
        handle_error("Erro ao carregar dados das empresas", e) 