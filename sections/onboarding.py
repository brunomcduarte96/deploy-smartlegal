import streamlit as st
from utils.auth_manager import check_authentication
from utils.supabase_manager import SupabaseManager
from utils.google_manager import GoogleManager
from utils.pdf_manager import PDFManager
import io
from datetime import datetime
import pytz
from utils.error_handler import handle_error
import logging
from utils.date_utils import data_por_extenso
from utils.text_utils import format_title_case
import locale

# Definir timezone de São Paulo
SP_TZ = pytz.timezone('America/Sao_Paulo')

logger = logging.getLogger(__name__)

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
    st.markdown(f"""
        <h3 style="
            color: #262730;
            margin-top: 20px;
            margin-bottom: 10px;
            padding-bottom: 5px;
        ">{title}</h3>
    """, unsafe_allow_html=True)

def handle_file_upload(file, folder_id: str, google_manager: GoogleManager):
    """Processa o upload de arquivo, convertendo para PDF se necessário"""
    if file is not None:
        try:
            file_content = file.read()
            file_type = file.name.split('.')[-1].lower()
            
            # Se já é PDF, não precisa converter
            if file_type == 'pdf':
                mime_type = 'application/pdf'
                final_content = file_content
            else:
                # Converte para PDF se não for PDF
                mime_type = 'application/pdf'
                final_content = PDFManager.convert_to_pdf(file_content, file_type)
            
            # Upload para o Google Drive com timestamp SP
            sp_timestamp = get_sp_datetime().strftime('%Y%m%d_%H%M%S')
            file_name = f"{sp_timestamp}_{file.name}"
            if not file_name.lower().endswith('.pdf'):
                file_name = f"{file_name}.pdf"
                
            file_id = google_manager.upload_file(
                file_name=file_name,
                file_content=final_content,
                mime_type=mime_type,
                folder_id=folder_id
            )
            logger.info(f"Arquivo {file_name} enviado com sucesso")
            return file_id
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file.name}: {str(e)}")
            st.error(f"Erro ao processar arquivo {file.name}")
            return None
    return None

def render_onboarding():
    st.title("Onboarding de Clientes")
    
    # Inicialização dos gerenciadores
    supabase_manager, google_manager = init_managers()
    
    # Controle de estado para mostrar formulário completo
    if 'show_full_form' not in st.session_state:
        st.session_state.show_full_form = False
    
    # Se não estiver mostrando o formulário completo, mostra a busca
    if not st.session_state.show_full_form:
        # Seção de busca de cliente
        st.header("Verificar Cliente Existente")
        
        # Campo de busca com autocomplete
        search_name = st.text_input("Digite o nome do cliente")
        
        if search_name:
            # Buscar sugestões de clientes
            suggestions = supabase_manager.search_clients_by_partial_name(search_name)
            
            if suggestions:
                # Criar lista de opções para o selectbox
                options = ["Selecione um cliente..."] + [
                    f"{cliente['nome_completo']} - CPF: {cliente['cpf']}" 
                    for cliente in suggestions
                ]
                
                selected_option = st.selectbox(
                    "Clientes encontrados:",
                    options
                )
                
                # Se um cliente foi selecionado
                if selected_option != "Selecione um cliente...":
                    # Encontrar o cliente selecionado
                    nome_selecionado = selected_option.split(" - CPF:")[0]
                    cliente = supabase_manager.get_client_by_name(nome_selecionado)
                    
                    if cliente:
                        st.success(f"Cliente selecionado: {cliente['nome_completo']}")
                        
                        # Mostrar dados do cliente (não editáveis)
                        with st.expander("Dados do Cliente", expanded=True):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_input("Nome Completo", value=cliente['nome_completo'], disabled=True)
                                st.text_input("Email", value=cliente['email'], disabled=True)
                                st.text_input("CPF", value=cliente['cpf'], disabled=True)
                            with col2:
                                st.text_input("Telefone", value=cliente['celular'], disabled=True)
                                st.text_input("Endereço", value=cliente['endereco'], disabled=True)
                        
                        # Formulário apenas para o caso
                        with st.form("caso_form"):
                            st.header("Novo Caso")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                caso = st.selectbox("Caso", [
                                    "Aéreo",
                                    "Trânsito",
                                    "Outros"
                                ])
                            with col2:
                                assunto_caso = st.selectbox("Assunto do Caso", [
                                    "Atraso de Voo",
                                    "Cancelamento de Voo",
                                    "Overbooking",
                                    "Downgrade",
                                    "Extravio de Bagagem",
                                    "Danos de Bagagem",
                                    "Multas",
                                    "Lei Seca",
                                    "Outros"
                                ])
                            with col3:
                                responsavel_comercial = st.selectbox("Responsável Comercial", [
                                    "Bruno",
                                    "Poppe",
                                    "Motta",
                                    "Caval",
                                    "Fred",
                                    "Mari",
                                    "Outro"
                                ])
                            
                            # Documentos
                            st.header("Documentos do Caso")
                            doc_identidade = st.file_uploader("Documento de Identidade", type=['pdf', 'png', 'jpg', 'jpeg'])
                            doc_residencia = st.file_uploader("Comprovante de Residência", type=['pdf', 'png', 'jpg', 'jpeg'])
                            outros_docs = st.file_uploader("Outros Documentos", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)
                            
                            submitted = st.form_submit_button("Cadastrar Novo Caso")
                            
                            if submitted:
                                try:
                                    # Criar barra de progresso
                                    progress_bar = st.progress(0)
                                    status_text = st.empty()

                                    # 1. Criando pasta do caso (20%)
                                    status_text.text("Criando pasta do caso...")
                                    progress_bar.progress(20)
                                    
                                    client_folder_id = cliente['pasta_drive_id']
                                    case_folder_id = google_manager.create_case_folder(client_folder_id, assunto_caso)
                                    
                                    # 2. Salvando dados do caso (40%)
                                    status_text.text("Salvando dados do caso...")
                                    progress_bar.progress(40)
                                    
                                    case_data = {
                                        'cliente_id': cliente['id'],
                                        'nome_cliente': cliente['nome_completo'],
                                        'caso': caso,
                                        'assunto_caso': assunto_caso,
                                        'responsavel_comercial': responsavel_comercial,
                                        'pasta_caso_id': case_folder_id,
                                        'pasta_caso_url': google_manager.get_folder_url(case_folder_id),
                                        'created_at': get_sp_datetime().isoformat()
                                    }
                                    
                                    # Salvar caso
                                    supabase_manager.insert_client_data('casos', case_data)
                                    
                                    # 3. Upload de documentos (60%)
                                    status_text.text("Fazendo upload dos documentos...")
                                    progress_bar.progress(60)
                                    
                                    # Upload documentos com tratamento de erro individual
                                    if doc_identidade:
                                        try:
                                            handle_file_upload(doc_identidade, case_folder_id, google_manager)
                                        except Exception as e:
                                            logger.error(f"Erro ao processar {doc_identidade.name}: {str(e)}")
                                            st.warning(f"Erro ao processar {doc_identidade.name}")

                                    if doc_residencia:
                                        try:
                                            handle_file_upload(doc_residencia, case_folder_id, google_manager)
                                        except Exception as e:
                                            logger.error(f"Erro ao processar {doc_residencia.name}: {str(e)}")
                                            st.warning(f"Erro ao processar {doc_residencia.name}")

                                    for doc in outros_docs:
                                        try:
                                            handle_file_upload(doc, case_folder_id, google_manager)
                                        except Exception as e:
                                            logger.error(f"Erro ao processar {doc.name}: {str(e)}")
                                            st.warning(f"Erro ao processar {doc.name}")
                                    
                                    # 4. Gerando procuração (80%)
                                    status_text.text("Gerando procuração...")
                                    progress_bar.progress(80)
                                    
                                    # Prepara dados para o template
                                    template_data = {
                                        'nome_completo': cliente['nome_completo'],
                                        'nacionalidade': cliente['nacionalidade'],
                                        'estado_civil': cliente['estado_civil'],
                                        'profissao': cliente['profissao'],
                                        'rg': cliente['rg'],
                                        'cpf': cliente['cpf'],
                                        'endereco': cliente['endereco'],
                                        'bairro': cliente['bairro'],
                                        'cep': cliente['cep'],
                                        'cidade': cliente['cidade'],
                                        'estado': cliente['estado'],
                                        'data_extenso': data_por_extenso(get_sp_datetime())
                                    }

                                    # Gera os documentos
                                    pdf_id, docx_id = google_manager.fill_document_template(
                                        "Modelo Procuracao JEC.docx",
                                        template_data,
                                        case_folder_id
                                    )
                                    
                                    # 5. Atualizando planilhas (90%)
                                    status_text.text("Atualizando planilhas...")
                                    progress_bar.progress(90)
                                    
                                    # Atualizar planilhas
                                    google_manager.update_sheets_with_client_data(
                                        client_data=cliente,
                                        folder_url=google_manager.get_folder_url(client_folder_id),
                                        caso_data=case_data,
                                        is_new_client=False
                                    )
                                    
                                    # 6. Finalização (100%)
                                    progress_bar.progress(100)
                                    status_text.text("Concluído!")
                                    st.success("Novo caso cadastrado com sucesso!")
                                    
                                except Exception as e:
                                    handle_error(e)
                                    st.stop()
            
            else:
                st.warning("Nenhum cliente encontrado com esse nome.")
                if st.button("Cadastrar Novo Cliente"):
                    st.session_state.show_full_form = True
                    st.rerun()
        
        else:
            st.info("👆 Digite o nome do cliente para verificar se já existe cadastro.")
    
    # Se estiver mostrando o formulário completo
    else:
        if st.button("← Voltar à Busca"):
            st.session_state.show_full_form = False
            st.rerun()
        else:
            render_full_form(supabase_manager, google_manager)

def render_full_form(supabase_manager: SupabaseManager, google_manager: GoogleManager):
    """Renderiza o formulário completo de cadastro de cliente"""
    with st.form("onboarding_form"):
        try:
            # Seção: Dados do Cliente
            create_form_section("Dados do Cliente")
            col1, col2 = st.columns(2)
            with col1:
                nome_completo = st.text_input("Nome Completo*")
                nacionalidade = st.text_input("Nacionalidade*", value="Brasileiro(a)")
                estado_civil = st.selectbox("Estado Civil*", 
                    ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
                profissao = st.text_input("Profissão*")
                email = st.text_input("E-mail*")
            
            with col2:
                celular = st.text_input("Celular*")
                data_nascimento = st.date_input("Data de Nascimento*")
                rg = st.text_input("RG*")
                cpf = st.text_input("CPF*")
            
            # Seção: Informações do Caso
            create_form_section("Informações do Caso")
            col_caso1, col_caso2, col_caso3 = st.columns(3)
            
            with col_caso1:
                caso = st.selectbox("Caso*", [
                    "Aéreo",
                    "Trânsito",
                    "Outros"
                ])
                
            with col_caso2:
                assunto_caso = st.selectbox("Assunto do Caso*", [
                    "Atraso de Voo",
                    "Cancelamento de Voo",
                    "Overbooking",
                    "Downgrade",
                    "Extravio de Bagagem",
                    "Danos de Bagagem",
                    "Multas",
                    "Lei Seca",
                    "Outros"
                ])
                
            with col_caso3:
                responsavel_comercial = st.selectbox("Responsável Comercial*", [
                    "Bruno",
                    "Poppe",
                    "Motta",
                    "Caval",
                    "Fred",
                    "Mari",
                    "Outro"
                ])
            
            # Seção: Endereço
            create_form_section("Endereço")
            col3, col4 = st.columns(2)
            with col3:
                endereco = st.text_input("Endereço Completo*")
                bairro = st.text_input("Bairro*")
                cidade = st.text_input("Cidade*")
            
            with col4:
                estado = st.selectbox("Estado*", [
                    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", 
                    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", 
                    "SP", "SE", "TO"
                ])
                cep = st.text_input("CEP*")
            
            # Seção: Documentos
            create_form_section("Documentos")
            doc_identidade = st.file_uploader("Documento de Identidade*", type=['pdf', 'png', 'jpg', 'jpeg'])
            doc_residencia = st.file_uploader("Comprovante de Residência*", type=['pdf', 'png', 'jpg', 'jpeg'])
            outros_docs = st.file_uploader("Outros Documentos", type=['pdf', 'png', 'jpg', 'jpeg'], accept_multiple_files=True)
            
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted:
                # Validar campos obrigatórios
                required_fields = {
                    'Nome Completo': nome_completo,
                    'Nacionalidade': nacionalidade,
                    'Estado Civil': estado_civil,
                    'Profissão': profissao,
                    'E-mail': email,
                    'Celular': celular,
                    'Data de Nascimento': data_nascimento,
                    'RG': rg,
                    'CPF': cpf,
                    'Endereço': endereco,
                    'Bairro': bairro,
                    'Cidade': cidade,
                    'Estado': estado,
                    'CEP': cep,
                    'Documento de Identidade': doc_identidade,
                    'Comprovante de Residência': doc_residencia
                }
                
                # Verificar campos vazios
                missing_fields = [field for field, value in required_fields.items() if not value]
                if missing_fields:
                    st.error(f"Por favor, preencha os seguintes campos obrigatórios: {', '.join(missing_fields)}")
                    return
                
                try:
                    # Verificar se o CPF já existe
                    existing_client = supabase_manager.get_client_by_cpf(cpf)
                    if existing_client:
                        st.error(f"""
                            CPF já cadastrado para o cliente: {existing_client['nome_completo']}
                            
                            Se você deseja adicionar um novo caso para este cliente, 
                            por favor use a busca de clientes na tela inicial.
                        """)
                        return
                    
                    # Criar barra de progresso
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 1. Formatação e preparação dos dados (10%)
                    status_text.text("Preparando dados...")
                    progress_bar.progress(10)
                    
                    # Log dos dados antes da formatação
                    logger.info("Dados recebidos do formulário:")
                    logger.info(f"Nome: {nome_completo}")
                    logger.info(f"CPF: {cpf}")
                    
                    # Formata os dados
                    nome_completo = format_title_case(nome_completo)
                    nacionalidade = format_title_case(nacionalidade)
                    profissao = format_title_case(profissao)
                    bairro = format_title_case(bairro)
                    cidade = format_title_case(cidade)
                    
                    sp_now = get_sp_datetime()
                    
                    # 2. Criação da estrutura no Drive (30%)
                    status_text.text("Criando estrutura de pastas...")
                    progress_bar.progress(30)
                    
                    try:
                        # Criar/buscar pasta do cliente
                        client_folder_id = google_manager.get_or_create_client_folder(nome_completo, cpf)
                        logger.info(f"Pasta do cliente criada/encontrada: {client_folder_id}")
                    except Exception as e:
                        logger.error(f"Erro ao criar pasta do cliente: {str(e)}")
                        raise Exception("Erro ao criar pasta do cliente no Google Drive")
                    
                    # 3. Salvando cliente no Supabase (50%)
                    status_text.text("Salvando dados do cliente...")
                    progress_bar.progress(50)
                    
                    client_data = {
                        'nome_completo': nome_completo,
                        'nacionalidade': nacionalidade,
                        'estado_civil': estado_civil,
                        'profissao': profissao,
                        'email': email,
                        'celular': celular,
                        'data_nascimento': data_nascimento.isoformat(),
                        'rg': rg,
                        'cpf': cpf,
                        'endereco': endereco,
                        'bairro': bairro,
                        'cidade': cidade,
                        'estado': estado,
                        'cep': cep,
                        'pasta_drive_id': client_folder_id,
                        'created_at': sp_now.isoformat()
                    }

                    # Salvar cliente no Supabase
                    client_response = supabase_manager.insert_client_data('clientes', client_data)
                    client_id = client_response['id']

                    # 4. Criando caso (70%)
                    status_text.text("Criando novo caso...")
                    progress_bar.progress(70)
                    
                    # Criar pasta do caso
                    case_folder_id = google_manager.create_case_folder(client_folder_id, assunto_caso)

                    # Preparar dados do caso
                    case_data = {
                        'cliente_id': client_id,
                        'nome_cliente': nome_completo,
                        'caso': caso,
                        'assunto_caso': assunto_caso,
                        'responsavel_comercial': responsavel_comercial,
                        'pasta_caso_id': case_folder_id,
                        'pasta_caso_url': google_manager.get_folder_url(case_folder_id),
                        'created_at': sp_now.isoformat()
                    }

                    # Salvar caso no Supabase
                    supabase_manager.insert_client_data('casos', case_data)

                    # 5. Upload de documentos (80%)
                    status_text.text("Fazendo upload dos documentos...")
                    progress_bar.progress(80)
                    
                    # Upload dos documentos na pasta do caso
                    doc_ids = {
                        'identidade': handle_file_upload(doc_identidade, case_folder_id, google_manager),
                        'residencia': handle_file_upload(doc_residencia, case_folder_id, google_manager),
                        'outros': [handle_file_upload(doc, case_folder_id, google_manager) 
                                 for doc in outros_docs if doc is not None]
                    }
                    
                    # 6. Gerando procuração (90%)
                    status_text.text("Gerando procuração...")
                    progress_bar.progress(90)
                    
                    # Prepara dados para o template
                    template_data = {
                        'nome_completo': nome_completo,
                        'nacionalidade': nacionalidade,
                        'estado_civil': estado_civil,
                        'profissao': profissao,
                        'rg': rg,
                        'cpf': cpf,
                        'endereco': endereco,
                        'bairro': bairro,
                        'cep': cep,
                        'cidade': cidade,
                        'estado': estado,
                        'data_extenso': data_por_extenso(sp_now)
                    }

                    # Gera os documentos
                    pdf_id, docx_id = google_manager.fill_document_template(
                        "Modelo Procuracao JEC.docx",
                        template_data,
                        case_folder_id  # Salva na pasta do caso
                    )
                    
                    # 7. Atualizando planilhas (95%)
                    status_text.text("Atualizando planilhas...")
                    progress_bar.progress(95)
                    
                    # Atualizar planilhas
                    google_manager.update_sheets_with_client_data(
                        client_data=client_data,
                        folder_url=google_manager.get_folder_url(client_folder_id),
                        caso_data=case_data,
                        is_new_client=True
                    )
                    
                    # 8. Finalização (100%)
                    progress_bar.progress(100)
                    status_text.text("Concluído!")
                    st.success("Cliente e caso cadastrados com sucesso!")
                    
                except Exception as e:
                    if "duplicate key value" in str(e) and "clientes_cpf_key" in str(e):
                        st.error("""
                            Este CPF já está cadastrado. 
                            Se você deseja adicionar um novo caso para este cliente,
                            por favor use a busca de clientes na tela inicial.
                        """)
                    else:
                        logger.error(f"Erro durante o cadastro: {str(e)}")
                        st.error(f"Erro durante o cadastro: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Erro ao renderizar formulário: {str(e)}")
            st.error(f"Erro ao renderizar formulário: {str(e)}")

def data_por_extenso(data):
    """Formata a data por extenso manualmente"""
    try:
        # Tentar configurar o locale para português
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
            except:
                # Se não conseguir configurar o locale, usar formato manual
                meses = {
                    1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
                    5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
                    9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
                }
                
                dia = str(data.day)
                mes = meses[data.month]
                ano = str(data.year)
                
                return f"{dia} de {mes} de {ano}"
                
        # Se conseguiu configurar o locale, usar strftime
        return data.strftime("%d de %B de %Y")
        
    except Exception as e:
        logger.error(f"Erro ao formatar data por extenso: {str(e)}")
        # Retornar formato básico em caso de erro
        return data.strftime("%d/%m/%Y")

if __name__ == "__main__":
    if not check_authentication(init_managers()[0].supabase):
        st.stop()
    render_onboarding() 