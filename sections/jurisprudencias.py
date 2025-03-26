import streamlit as st
from utils.supabase_manager import SupabaseManager
from datetime import datetime
import pandas as pd

def process_jurisprudencia_update(edited_rows, original_rows):
    """Process updates to jurisprudencia data"""
    supabase = SupabaseManager()
    
    try:
        for index, changes in edited_rows.items():
            if not changes:  # Skip if no changes
                continue
                
            original_row = original_rows.iloc[index]
            jurisprudencia_id = original_row['id']
            
            # Update the jurisprudencia in Supabase
            try:
                supabase.update_jurisprudencia(jurisprudencia_id, changes)
                st.success(f"Jurisprudência atualizada com sucesso!")
            except Exception as e:
                st.error(f"Erro ao atualizar jurisprudência: {str(e)}")
        
    except Exception as e:
        st.error(f"Erro ao atualizar dados da jurisprudência: {str(e)}")

def add_new_jurisprudencia():
    """Add a new jurisprudencia"""
    st.subheader("Adicionar Nova Jurisprudência")
    
    with st.form("new_jurisprudencia_form"):
        nome = st.text_input("Nome")
        texto = st.text_area("Texto")
        secao = st.text_input("Seção")
        
        submitted = st.form_submit_button("Adicionar")
        
        if submitted:
            if not nome or not texto or not secao:
                st.error("Todos os campos são obrigatórios")
                return
                
            try:
                supabase = SupabaseManager()
                new_jurisprudencia = {
                    'nome': nome,
                    'texto': texto,
                    'secao': secao,
                    'created_at': datetime.now().isoformat()
                }
                
                supabase.add_jurisprudencia(new_jurisprudencia)
                st.success("Jurisprudência adicionada com sucesso!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao adicionar jurisprudência: {str(e)}")

def render_jurisprudencias():
    """Render the jurisprudencias page"""
    st.title("Jurisprudências")
    
    # Add jurisprudencia button
    if st.button("+ Adicionar Nova Jurisprudência"):
        st.session_state.show_add_jurisprudencia = True
        
    # Show add jurisprudencia form
    if st.session_state.get('show_add_jurisprudencia', False):
        add_new_jurisprudencia()
        st.divider()
    
    supabase = SupabaseManager()
    
    try:
        # Fetch jurisprudencias data
        jurisprudencias = supabase.get_all_jurisprudencias()
        
        if not jurisprudencias:
            st.info("Nenhuma jurisprudência cadastrada.")
            return
            
        # Convert to DataFrame
        df = pd.DataFrame(jurisprudencias)
        
        # Format created_at column
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at']).dt.date
        
        # Create a copy of original data for comparison
        original_df = df.copy()
        
        # Reorder columns
        columns_order = ['id', 'created_at', 'nome', 'texto', 'secao']
        df = df.reindex(columns=columns_order)
        
        # Rename columns
        column_names = {
            'id': 'ID',
            'created_at': 'Data de Criação',
            'nome': 'Nome',
            'texto': 'Texto',
            'secao': 'Seção'
        }
        df = df.rename(columns=column_names)
        
        # Sort by Seção
        df = df.sort_values('Seção')
        
        # Get visible columns (excluding 'ID')
        visible_columns = [col for col in df.columns if col != 'ID']
        
        # Display editable table
        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_order=visible_columns,
            key="jurisprudencia_editor",
            disabled=['ID', 'Data de Criação'],
            on_change=lambda: st.session_state.update({'data_editor_changed': True})
        )
        
        # Process any edits
        if st.session_state.get('data_editor_changed', False):
            edited_rows = {}
            
            # Compare original and edited dataframes
            for idx, row in edited_df.iterrows():
                changes = {}
                original_row = original_df.iloc[idx]
                
                # Check each column for changes
                for col in ['nome', 'texto', 'secao']:
                    new_value = row[column_names[col]]
                    if new_value != original_row[col]:
                        changes[col] = new_value
                
                if changes:  # If there are changes for this row
                    edited_rows[idx] = changes
            
            if edited_rows:
                process_jurisprudencia_update(edited_rows, original_df)
                st.session_state.data_editor_changed = False
                st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao carregar jurisprudências: {str(e)}") 