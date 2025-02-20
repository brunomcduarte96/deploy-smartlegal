import streamlit as st
from utils.auth_manager import check_authentication
from utils.supabase_manager import SupabaseManager
from utils.google_manager import GoogleManager
from utils.pdf_manager import PDFManager
import io
from datetime import datetime
import pytz

# Definir timezone de São Paulo
SP_TZ = pytz.timezone('America/Sao_Paulo')

def get_sp_datetime():
    """Retorna a data e hora atual no timezone de São Paulo"""
    return datetime.now(SP_TZ)

def format_sp_datetime(dt):
    """Formata a data e hora no padrão brasileiro"""
    return dt.strftime('%d/%m/%Y %H:%M:%S')

def init_managers():
    """Inicializa os gerenciadores necessários"""
    return SupabaseManager(), GoogleManager()

def create_form_section(title: str):
    """Cria uma seção do formulário com estilo consistente"""
    st.markdown(f"### {title}")
    st.markdown("---")

def handle_file_upload(file, folder_id: str, google_manager: GoogleManager):
    """Processa o upload de arquivo, convertendo para PDF se necessário"""
    if file is not None:
        file_content = file.read()
        file_type = file.name.split('.')[-1].lower()
        
        # Verifica se é PDF ou precisa converter
        if not PDFManager.check_pdf(file_content):
            try:
                file_content = PDFManager.convert_to_pdf(file_content, file_type)
            except Exception as e:
                st.error(f"Erro ao converter arquivo para PDF: {str(e)}")
                return None
        
        # Upload para o Google Drive com timestamp SP
        try:
            sp_timestamp = get_sp_datetime().strftime('%Y%m%d_%H%M%S')
            file_name = f"{sp_timestamp}_{file.name}.pdf"
            file_id = google_manager.upload_file(
                file_name=file_name,
                file_content=file_content,
                mime_type='application/pdf',
                folder_id=folder_id
            )
            return file_id
        except Exception as e:
            st.error(f"Erro ao fazer upload do arquivo: {str(e)}")
            return None
    return None

def main():
    st.title("Onboarding de Clientes")
    
    # Inicialização dos gerenciadores
    supabase_manager, google_manager = init_managers()
    
    # Formulário principal
    with st.form("onboarding_form"):
        # Seção: Dados do Cliente
        create_form_section("Dados do Cliente")
        col1, col2 = st.columns(2)
        with col1:
            nome_completo = st.text_input("Nome Completo")
            nacionalidade = st.text_input("Nacionalidade")
            estado_civil = st.selectbox("Estado Civil", 
                ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
            profissao = st.text_input("Profissão")
            email = st.text_input("E-mail")
        
        with col2:
            celular = st.text_input("Celular")
            data_nascimento = st.date_input("Data de Nascimento")
            rg = st.text_input("RG")
            cpf = st.text_input("CPF")
        
        # Seção: Informações do Caso
        create_form_section("Informações do Caso")
        caso = st.text_input("Caso")
        assunto_caso = st.text_area("Assunto do Caso")
        responsavel_comercial = st.text_input("Responsável Comercial")
        
        # Seção: Endereço
        create_form_section("Endereço")
        col3, col4 = st.columns(2)
        with col3:
            endereco = st.text_input("Endereço Completo")
            bairro = st.text_input("Bairro")
            cidade = st.text_input("Cidade")
        
        with col4:
            estado = st.selectbox("Estado", [
                "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
                "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
                "SP", "SE", "TO"
            ])
            cep = st.text_input("CEP")
        
        # Seção: Documentos
        create_form_section("Documentos")
        doc_identidade = st.file_uploader("Documento de Identidade", 
            type=['pdf', 'png', 'jpg', 'jpeg', 'docx'])
        doc_residencia = st.file_uploader("Comprovante de Residência", 
            type=['pdf', 'png', 'jpg', 'jpeg', 'docx'])
        outros_docs = st.file_uploader("Outros Comprovantes", 
            type=['pdf', 'png', 'jpg', 'jpeg', 'docx'], accept_multiple_files=True)
        
        # Botão de submissão
        submitted = st.form_submit_button("Cadastrar")
        
        if submitted:
            try:
                with st.spinner("Processando cadastro..."):
                    # 1. Criar pasta no Google Drive com timestamp SP
                    sp_now = get_sp_datetime()
                    folder_name = f"{nome_completo}_{sp_now.strftime('%Y%m%d_%H%M%S')}"
                    folder_id = google_manager.create_folder(folder_name)
                    
                    # 2. Processar documentos
                    doc_ids = {
                        'identidade': handle_file_upload(doc_identidade, folder_id, google_manager),
                        'residencia': handle_file_upload(doc_residencia, folder_id, google_manager),
                        'outros': [handle_file_upload(doc, folder_id, google_manager) 
                                 for doc in outros_docs if doc is not None]
                    }
                    
                    # 3. Preparar dados para o Supabase com data SP
                    client_data = {
                        'nome_completo': nome_completo,
                        'nacionalidade': nacionalidade,
                        'estado_civil': estado_civil,
                        'profissao': profissao,
                        'email': email,
                        'celular': celular,
                        'data_nascimento': data_nascimento.isoformat(),  # A data de nascimento não precisa de timezone
                        'rg': rg,
                        'cpf': cpf,
                        'caso': caso,
                        'assunto_caso': assunto_caso,
                        'responsavel_comercial': responsavel_comercial,
                        'endereco': endereco,
                        'bairro': bairro,
                        'cidade': cidade,
                        'estado': estado,
                        'cep': cep,
                        'pasta_drive_id': folder_id,
                        'documentos': doc_ids,
                        'created_at': sp_now.isoformat()  # Adiciona timestamp SP
                    }
                    
                    # 4. Salvar no Supabase
                    supabase_manager.insert_client_data('clientes', client_data)
                    
                    # 5. Atualizar planilhas do Google Sheets
                    google_manager.update_sheets_with_client_data(client_data)
                    
                    # 6. Preencher template do Google Docs
                    template_data = {
                        'nome': nome_completo,
                        'cpf': cpf,
                        'endereco': f"{endereco}, {bairro}, {cidade}/{estado}",
                        'caso': caso,
                        'data': format_sp_datetime(sp_now).split()[0]  # Apenas a data no formato BR
                    }
                    doc_id = google_manager.fill_document_template(
                        st.secrets["TEMPLATE_DOC_ID"], 
                        template_data
                    )
                    
                    # 7. Converter documento preenchido para PDF e salvar no Drive
                    pdf_content = google_manager.export_to_pdf(doc_id)
                    google_manager.upload_file(
                        f"contrato_{nome_completo}.pdf",
                        pdf_content,
                        'application/pdf',
                        folder_id
                    )
                    
                    st.success("Cliente cadastrado com sucesso!")
                    
            except Exception as e:
                st.error(f"Erro ao processar cadastro: {str(e)}")

if __name__ == "__main__":
    if not check_authentication(init_managers()[0].supabase):
        st.stop()
    main() 