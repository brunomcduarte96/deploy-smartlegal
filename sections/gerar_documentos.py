import streamlit as st
from utils.supabase_manager import SupabaseManager
from utils.google_manager import GoogleManager
from utils.auth_manager import check_authentication
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
from googleapiclient.http import MediaIoBaseDownload
import pytz
from datetime import datetime
from utils.date_utils import data_por_extenso

logger = logging.getLogger(__name__)

def search_client(search_term, supabase):
    """Busca clientes pelo nome com autocomplete"""
    if not search_term:
        return []
    
    try:
        clients = supabase.search_clients_by_partial_name(search_term)
        return clients
    except Exception as e:
        logger.error(f"Erro ao buscar clientes: {str(e)}")
        return []

def send_email(client_data, case_data, google_manager):
    """Envia e-mail com procuração e contrato de honorários"""
    try:
        # Configurações de e-mail do secrets
        email_host = st.secrets["EMAIL_HOST"]
        email_port = st.secrets["EMAIL_PORT"]
        email_user = st.secrets["EMAIL_USER"]
        email_password = st.secrets["EMAIL_PASSWORD"]
        email_from = st.secrets["EMAIL_FROM"]
        
        # Obter o ID da pasta do caso
        case_folder_id = case_data.get('pasta_caso_id')
        if not case_folder_id:
            raise Exception("ID da pasta do caso não encontrado")
        
        # Buscar arquivos na pasta do caso
        files = google_manager.drive_service.files().list(
            q=f"'{case_folder_id}' in parents and (name contains 'Procuracao' or name contains 'Contrato de Honorarios')",
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute().get('files', [])
        
        # Filtrar para encontrar os arquivos PDF
        procuracao_pdf = next((f for f in files if 'Procuracao' in f['name'] and f['mimeType'] == 'application/pdf'), None)
        contrato_pdf = next((f for f in files if 'Contrato de Honorarios' in f['name'] and f['mimeType'] == 'application/pdf'), None)
        
        if not procuracao_pdf or not contrato_pdf:
            raise Exception("Documentos não encontrados na pasta do caso")
        
        # Baixar os arquivos
        procuracao_content = io.BytesIO()
        contrato_content = io.BytesIO()
        
        # Download da procuração
        request = google_manager.drive_service.files().get_media(fileId=procuracao_pdf['id'])
        downloader = MediaIoBaseDownload(procuracao_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Download do contrato
        request = google_manager.drive_service.files().get_media(fileId=contrato_pdf['id'])
        downloader = MediaIoBaseDownload(contrato_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Preparar o e-mail
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = client_data['email']
        msg['Subject'] = f"Procuração e Contrato de Honorários - Smart Legal e {client_data['nome_completo']}"
        
        # Template HTML para o corpo do e-mail com CSS inline
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2c3e50; margin-bottom: 5px;">Smart Legal</h2>
                    <div style="height: 3px; background-color: #3498db; width: 100px; margin: 0 auto;"></div>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <p style="margin-bottom: 15px;">Prezada(o) <strong>{client_data['nome_completo']}</strong>,</p>
                    
                    <p style="margin-bottom: 15px;">Encaminhamos em anexo {"três" if include_declaracao else "dois"} documentos importantes para o início do seu atendimento:</p>
                    
                    <ul style="margin-bottom: 20px; padding-left: 20px;">
                        <li style="margin-bottom: 10px;"><strong>Procuração</strong>, que deverá ser assinada por meio da plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a>;</li>
                        <li style="margin-bottom: 10px;"><strong>Contrato de Prestação de Serviços e Fixação de Honorários</strong>;</li>
                        {f'<li style="margin-bottom: 10px;"><strong>Declaração de Residência</strong>, que deverá ser assinada pelo parente que está cedendo o comprovante.</li>' if include_declaracao else ''}
                    </ul>
                    
                    <div style="background-color: #f8f9fa; border-left: 4px solid #e74c3c; padding: 15px; margin-bottom: 20px;">
                        <p style="margin: 0; color: #e74c3c;"><strong>🔒 Atenção:</strong> somente após o recebimento da procuração assinada poderemos dar andamento ao seu caso.</p>
                    </div>
                    
                    <p style="margin-bottom: 15px;">Solicitamos, por gentileza, que realize os seguintes passos:</p>
                    
                    <ol style="margin-bottom: 20px; padding-left: 25px;">
                        <li style="margin-bottom: 10px;">Assine a procuração na plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a> e nos devolva assinada.</li>
                        {f'<li style="margin-bottom: 10px;">Seu parente assine a declaração de residência na plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a> e nos devolva assinada.</li>' if include_declaracao else ''}
                        <li style="margin-bottom: 10px;">Responder este e-mail com um de acordo sobre o contrato de honorários.</li>
                    </ol>
                    
                    <p style="margin-bottom: 15px;">Permanecemos à disposição para qualquer dúvida que possa surgir.</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eeeeee;">
                    <p style="margin: 0;">Atenciosamente,</p>
                    <p style="margin: 0; font-weight: bold; color: #2c3e50;">Equipe Smart Legal</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Anexar o corpo do e-mail
        msg.attach(MIMEText(html_template, 'html'))
        
        # Anexar a procuração
        procuracao_content.seek(0)
        procuracao_attachment = MIMEApplication(procuracao_content.read(), _subtype="pdf")
        procuracao_attachment.add_header('Content-Disposition', 'attachment', filename=f"Procuracao_{client_data['nome_completo']}.pdf")
        msg.attach(procuracao_attachment)
        
        # Anexar o contrato
        contrato_content.seek(0)
        contrato_attachment = MIMEApplication(contrato_content.read(), _subtype="pdf")
        contrato_attachment.add_header('Content-Disposition', 'attachment', filename=f"Contrato de Honorarios - {client_data['nome_completo']}.pdf")
        msg.attach(contrato_attachment)
        
        # Enviar o e-mail
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        raise Exception(f"Erro ao enviar e-mail: {str(e)}")

def render_gerar_documentos():
    """Renderiza a página de Enviar Email"""
    st.title("Enviar Email")
    
    # Inicializar gerenciadores
    supabase = SupabaseManager()
    google_manager = GoogleManager()
    
    # Seção de seleção do cliente
    st.markdown("### 1. Selecionar Cliente")
    
    # Campo de busca do cliente
    search_term = st.text_input("Buscar cliente por nome:")
    
    if search_term:
        clients = search_client(search_term, supabase)
        if clients:
            # Criar lista de opções para o selectbox
            client_options = {
                f"{client['nome_completo']} - {client['cpf']}": client 
                for client in clients
            }
            
            # Dropdown para seleção do cliente
            selected_client = st.selectbox(
                "Selecione o cliente:",
                options=list(client_options.keys()),
                key="client_select"
            )
            
            if selected_client:
                # Salvar dados do cliente selecionado
                st.session_state.selected_client_data = client_options[selected_client]
                
                # Mostrar dados do cliente selecionado
                st.write("**Dados do cliente selecionado:**")
                
                # Criar duas colunas
                col1, col2 = st.columns(2)
                
                # Filtrar campos que queremos mostrar (excluindo 'id')
                campos = {k: v for k, v in st.session_state.selected_client_data.items() if k != 'id'}
                
                # Dividir os campos em duas listas de tamanho igual
                total_campos = len(campos)
                metade = (total_campos + 1) // 2  # +1 para garantir que todos os campos sejam mostrados
                
                # Preencher as colunas
                with col1:
                    for i, (key, value) in enumerate(campos.items()):
                        if i < metade:
                            st.write(f"**{key}:** {value}")
                
                with col2:
                    for i, (key, value) in enumerate(campos.items()):
                        if i >= metade:
                            st.write(f"**{key}:** {value}")
                
                # Buscar casos do cliente
                client_cases = supabase.get_client_cases(st.session_state.selected_client_data['id'])
                
                if client_cases:
                    st.markdown("---")
                    st.write("**Selecione o caso:**")
                    
                    # Criar lista de opções para o selectbox de casos
                    case_options = {
                        f"{case.get('chave_caso', 'Sem chave')} - {case.get('assunto_caso', 'Sem assunto')}": case 
                        for case in client_cases
                    }
                    
                    # Dropdown para seleção do caso
                    selected_case = st.selectbox(
                        "Casos do cliente",
                        options=list(case_options.keys()),
                        key="case_select"
                    )
                    
                    if selected_case:
                        # Salvar dados do caso selecionado
                        st.session_state.selected_case_data = case_options[selected_case]
                        
                        # Mostrar informações do caso
                        st.write("**Detalhes do caso:**")
                        case_col1, case_col2 = st.columns(2)
                        
                        with case_col1:
                            st.write(f"**Nome do Cliente:** {st.session_state.selected_case_data.get('nome_cliente', 'Não informado')}")
                            st.write(f"**Caso:** {st.session_state.selected_case_data.get('caso', 'Não informado')}")
                            st.write(f"**Assunto:** {st.session_state.selected_case_data.get('assunto_caso', 'Não informado')}")
                            st.write(f"**Responsável:** {st.session_state.selected_case_data.get('responsavel_comercial', 'Não informado')}")
                        
                        with case_col2:
                            st.write(f"**Chave do Caso:** {st.session_state.selected_case_data.get('chave_caso', 'Não informado')}")
                            st.write(f"**ID da Pasta:** {st.session_state.selected_case_data.get('pasta_caso_id', 'Não informado')}")
                            if pasta_url := st.session_state.selected_case_data.get('pasta_caso_url'):
                                st.write(f"**URL da Pasta:** [Acessar]({pasta_url})")
                            st.write(f"**Data de Criação:** {st.session_state.selected_case_data.get('created_at', 'Não informado')}")
                        
                        # Adicionar checkbox para Declaração de Residência
                        st.markdown("---")
                        st.markdown("### 2. Opções Adicionais")
                        
                        precisa_declaracao = st.checkbox("Cliente precisa de Declaração de Residência?")
                        
                        # Se checkbox ativado, mostrar formulário para dados do parente
                        dados_parente = {}
                        if precisa_declaracao:
                            st.markdown("#### Dados do Parente")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                dados_parente['nome_completo_parente'] = st.text_input("Nome Completo do Parente")
                                dados_parente['nacionalidade_parente'] = st.text_input("Nacionalidade do Parente")
                                dados_parente['estado_civil_parente'] = st.text_input("Estado Civil do Parente")
                            
                            with col2:
                                dados_parente['rg_parente'] = st.text_input("RG do Parente")
                                dados_parente['cpf_parente'] = st.text_input("CPF do Parente")
                        
                        # Botão para enviar e-mail
                        st.markdown("---")
                        if st.button("Enviar E-mail", type="primary"):
                            try:
                                with st.spinner("Preparando documentos..."):
                                    # Verificar se precisa gerar declaração de residência
                                    declaracao_id = None
                                    if precisa_declaracao:
                                        # Verificar se todos os campos do parente foram preenchidos
                                        campos_vazios = [k for k, v in dados_parente.items() if not v]
                                        if campos_vazios:
                                            st.error(f"Por favor, preencha todos os campos do parente: {', '.join(campos_vazios)}")
                                            st.stop()
                                        else:
                                            # Gerar declaração de residência e obter o ID
                                            declaracao_id = gerar_declaracao_residencia(
                                                st.session_state.selected_client_data,
                                                dados_parente,
                                                st.session_state.selected_case_data,
                                                google_manager
                                            )
                                            
                                            if not declaracao_id:
                                                st.error("Erro ao gerar declaração de residência")
                                                st.stop()
                                    
                                    # Enviar e-mail com ou sem declaração
                                    with st.spinner("Enviando e-mail..."):
                                        if send_email_with_declaracao(
                                            st.session_state.selected_client_data, 
                                            st.session_state.selected_case_data, 
                                            google_manager,
                                            precisa_declaracao,
                                            declaracao_id
                                        ):
                                            st.success(f"E-mail enviado com sucesso para {st.session_state.selected_client_data['email']}!")
                            except Exception as e:
                                st.error(f"Erro ao enviar e-mail: {str(e)}")
                else:
                    st.info("Nenhum caso encontrado para este cliente")
        else:
            st.info("Nenhum cliente encontrado com esse nome.")

def gerar_declaracao_residencia(client_data, parente_data, case_data, google_manager):
    """Gera a declaração de residência e retorna o ID do PDF"""
    try:
        # Obter o ID da pasta do caso
        case_folder_id = case_data.get('pasta_caso_id')
        if not case_folder_id:
            raise Exception("ID da pasta do caso não encontrado")
        
        # Obter a data atual em São Paulo
        sp_tz = pytz.timezone('America/Sao_Paulo')
        sp_now = datetime.now(sp_tz)
        
        # Preparar os dados para o template
        template_data = {
            # Dados do parente
            'nome_completo_parente': parente_data['nome_completo_parente'],
            'nacionalidade_parente': parente_data['nacionalidade_parente'],
            'estado_civil_parente': parente_data['estado_civil_parente'],
            'rg_parente': parente_data['rg_parente'],
            'cpf_parente': parente_data['cpf_parente'],
            
            # Dados do cliente
            'nome_completo': client_data['nome_completo'],
            'nacionalidade': client_data['nacionalidade'],
            'estado_civil': client_data['estado_civil'],
            'rg': client_data['rg'],
            'cpf': client_data['cpf'],
            
            # Endereço
            'endereco': client_data['endereco'],
            'bairro': client_data['bairro'],
            'cep': client_data['cep'],
            'cidade': client_data['cidade'],
            'estado': client_data['estado'],
            
            # Data
            'data_extenso': data_por_extenso(sp_now)
        }
        
        # Gerar a declaração usando o template com nome personalizado
        pdf_id, docx_id = google_manager.fill_document_template(
            "Declaracao de residencia.docx",
            template_data,
            case_folder_id,
            output_filename=f"Declaração de Residencia - {client_data['nome_completo']}"
        )
        
        # Verificar se o arquivo foi criado
        if not pdf_id:
            raise Exception("Falha ao gerar o PDF da declaração de residência")
            
        # Aguardar um momento para garantir que o arquivo esteja disponível
        import time
        time.sleep(2)
        
        # Verificar se o arquivo existe no Drive
        try:
            google_manager.drive_service.files().get(fileId=pdf_id).execute()
            logger.info(f"Declaração de residência gerada com sucesso. PDF ID: {pdf_id}")
            return pdf_id
        except Exception as e:
            logger.error(f"Arquivo gerado mas não encontrado no Drive: {str(e)}")
            raise Exception(f"Arquivo gerado mas não encontrado no Drive: {str(e)}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar declaração de residência: {str(e)}")
        raise Exception(f"Erro ao gerar declaração de residência: {str(e)}")

def send_email_with_declaracao(client_data, case_data, google_manager, include_declaracao=False, declaracao_id=None):
    """Envia e-mail com procuração, contrato de honorários e opcionalmente declaração de residência"""
    try:
        # Configurações de e-mail do secrets
        email_host = st.secrets["EMAIL_HOST"]
        email_port = st.secrets["EMAIL_PORT"]
        email_user = st.secrets["EMAIL_USER"]
        email_password = st.secrets["EMAIL_PASSWORD"]
        email_from = st.secrets["EMAIL_FROM"]
        
        # Obter o ID da pasta do caso
        case_folder_id = case_data.get('pasta_caso_id')
        if not case_folder_id:
            raise Exception("ID da pasta do caso não encontrado")
        
        # Buscar arquivos na pasta do caso
        files = google_manager.drive_service.files().list(
            q=f"'{case_folder_id}' in parents and (name contains 'Procuracao' or name contains 'Contrato de Honorarios')",
            spaces='drive',
            fields='files(id, name, mimeType)'
        ).execute().get('files', [])
        
        # Filtrar para encontrar os arquivos PDF
        procuracao_pdf = next((f for f in files if 'Procuracao' in f['name'] and f['mimeType'] == 'application/pdf'), None)
        contrato_pdf = next((f for f in files if 'Contrato de Honorarios' in f['name'] and f['mimeType'] == 'application/pdf'), None)
        
        if not procuracao_pdf or not contrato_pdf:
            raise Exception("Documentos obrigatórios não encontrados na pasta do caso")
        
        # Baixar os arquivos
        procuracao_content = io.BytesIO()
        contrato_content = io.BytesIO()
        declaracao_content = None
        
        # Download da procuração
        request = google_manager.drive_service.files().get_media(fileId=procuracao_pdf['id'])
        downloader = MediaIoBaseDownload(procuracao_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Download do contrato
        request = google_manager.drive_service.files().get_media(fileId=contrato_pdf['id'])
        downloader = MediaIoBaseDownload(contrato_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Download da declaração se necessário
        if include_declaracao and declaracao_id:
            declaracao_content = io.BytesIO()
            try:
                request = google_manager.drive_service.files().get_media(fileId=declaracao_id)
                downloader = MediaIoBaseDownload(declaracao_content, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            except Exception as e:
                logger.error(f"Erro ao baixar declaração de residência: {str(e)}")
                raise Exception(f"Erro ao baixar declaração de residência: {str(e)}")
        
        # Preparar o e-mail
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = client_data['email']
        msg['Subject'] = f"Procuração e Contrato de Honorários - Smart Legal e {client_data['nome_completo']}"
        
        # Template HTML para o corpo do e-mail com CSS inline
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; color: #333333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #2c3e50; margin-bottom: 5px;">Smart Legal</h2>
                    <div style="height: 3px; background-color: #3498db; width: 100px; margin: 0 auto;"></div>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <p style="margin-bottom: 15px;">Prezada(o) <strong>{client_data['nome_completo']}</strong>,</p>
                    
                    <p style="margin-bottom: 15px;">Encaminhamos em anexo {"três" if include_declaracao else "dois"} documentos importantes para o início do seu atendimento:</p>
                    
                    <ul style="margin-bottom: 20px; padding-left: 20px;">
                        <li style="margin-bottom: 10px;"><strong>Procuração</strong>, que deverá ser assinada por meio da plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a>;</li>
                        <li style="margin-bottom: 10px;"><strong>Contrato de Prestação de Serviços e Fixação de Honorários</strong>;</li>
                        {f'<li style="margin-bottom: 10px;"><strong>Declaração de Residência</strong>, que deverá ser assinada pelo parente que está cedendo o comprovante.</li>' if include_declaracao else ''}
                    </ul>
                    
                    <div style="background-color: #f8f9fa; border-left: 4px solid #e74c3c; padding: 15px; margin-bottom: 20px;">
                        <p style="margin: 0; color: #e74c3c;"><strong>🔒 Atenção:</strong> somente após o recebimento da procuração assinada poderemos dar andamento ao seu caso.</p>
                    </div>
                    
                    <p style="margin-bottom: 15px;">Solicitamos, por gentileza, que realize os seguintes passos:</p>
                    
                    <ol style="margin-bottom: 20px; padding-left: 25px;">
                        <li style="margin-bottom: 10px;">Assine a procuração na plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a> e nos devolva assinada.</li>
                        {f'<li style="margin-bottom: 10px;">Seu parente assine a declaração de residência na plataforma <a href="https://www.gov.br/pt-br/servicos/assinatura-eletronica" style="color: #3498db; text-decoration: none; font-weight: bold;">Gov.br</a> e nos devolva assinada.</li>' if include_declaracao else ''}
                        <li style="margin-bottom: 10px;">Responder este e-mail com um de acordo sobre o contrato de honorários.</li>
                    </ol>
                    
                    <p style="margin-bottom: 15px;">Permanecemos à disposição para qualquer dúvida que possa surgir.</p>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eeeeee;">
                    <p style="margin: 0;">Atenciosamente,</p>
                    <p style="margin: 0; font-weight: bold; color: #2c3e50;">Equipe Smart Legal</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Anexar o corpo do e-mail
        msg.attach(MIMEText(html_template, 'html'))
        
        # Anexar a procuração
        procuracao_content.seek(0)
        procuracao_attachment = MIMEApplication(procuracao_content.read(), _subtype="pdf")
        procuracao_attachment.add_header('Content-Disposition', 'attachment', filename=f"Procuracao_{client_data['nome_completo']}.pdf")
        msg.attach(procuracao_attachment)
        
        # Anexar o contrato
        contrato_content.seek(0)
        contrato_attachment = MIMEApplication(contrato_content.read(), _subtype="pdf")
        contrato_attachment.add_header('Content-Disposition', 'attachment', filename=f"Contrato de Honorarios - {client_data['nome_completo']}.pdf")
        msg.attach(contrato_attachment)
        
        # Anexar a declaração se necessário
        if include_declaracao and declaracao_content:
            declaracao_content.seek(0)
            declaracao_attachment = MIMEApplication(declaracao_content.read(), _subtype="pdf")
            declaracao_attachment.add_header('Content-Disposition', 'attachment', filename=f"Declaração de Residencia - {client_data['nome_completo']}.pdf")
            msg.attach(declaracao_attachment)
        
        # Enviar o e-mail
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        raise Exception(f"Erro ao enviar e-mail: {str(e)}")

if __name__ == "__main__":
    if not check_authentication(SupabaseManager().supabase):
        st.stop()
    render_gerar_documentos() 