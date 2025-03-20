import streamlit as st
from utils.supabase_manager import SupabaseManager
from utils.audio_manager import AudioManager  # Vamos criar esse módulo
from datetime import datetime
import logging
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

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

def render_client_section():
    """Renderiza a seção de seleção de cliente"""
    st.subheader("1. Dados do Cliente")
    
    supabase = SupabaseManager()
    
    # Campo de busca com autocomplete
    search_term = st.text_input("Buscar cliente pelo nome")
    
    if search_term:
        clients = search_client(search_term, supabase)
        
        if clients:
            # Criar lista de opções para o selectbox
            client_options = {f"{client['nome_completo']} ({client['email']})": client 
                            for client in clients}
            
            selected_client = st.selectbox(
                "Selecione o cliente",
                options=list(client_options.keys()),
                key="client_select"
            )
            
            if selected_client:
                # Salvar dados do cliente selecionado na session_state
                st.session_state.selected_client_data = client_options[selected_client]
                
                # Mostrar dados do cliente selecionado em 3 colunas
                st.write("**Cliente selecionado:**")
                col1, col2, col3 = st.columns(3)
                
                # Distribuir os campos entre as colunas
                client_data = {k: v for k, v in st.session_state.selected_client_data.items() if k != 'id'}
                fields = list(client_data.items())
                
                # Calcular quantos campos por coluna
                fields_per_col = len(fields) // 3 + (1 if len(fields) % 3 > 0 else 0)
                
                # Preencher as colunas
                with col1:
                    for key, value in fields[:fields_per_col]:
                        st.write(f"{key}: {value}")
                
                with col2:
                    for key, value in fields[fields_per_col:fields_per_col*2]:
                        st.write(f"{key}: {value}")
                
                with col3:
                    for key, value in fields[fields_per_col*2:]:
                        st.write(f"{key}: {value}")
                
                # Buscar casos do cliente
                client_cases = supabase.get_client_cases(st.session_state.selected_client_data['id'])
                
                if client_cases:
                    # Criar lista de opções para o selectbox de casos
                    case_options = {
                        f"{case.get('chave_caso', 'Sem chave')} - {case.get('assunto_caso', 'Sem assunto')}": case 
                        for case in client_cases
                    }
                    
                    st.markdown("---")
                    st.write("**Selecione o caso:**")
                    
                    selected_case = st.selectbox(
                        "Casos do cliente",
                        options=list(case_options.keys()),
                        key="case_select"
                    )
                    
                    if selected_case:
                        # Salvar dados do caso selecionado na session_state
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
                else:
                    st.info("Nenhum caso encontrado para este cliente")
        else:
            st.info("Nenhum cliente encontrado")

def render_company_section():
    """Renderiza a seção de seleção da empresa aérea"""
    st.markdown("---")
    st.subheader("2. Dados da Empresa Aérea")
    
    supabase = SupabaseManager()
    
    try:
        # Buscar todas as empresas
        companies = supabase.get_all_companies()
        
        if companies:
            # Criar lista de opções para o selectbox
            company_options = {company['nome']: company for company in companies}
            
            selected_company = st.selectbox(
                "Selecione a empresa aérea",
                options=list(company_options.keys()),
                key="company_select"
            )
            
            if selected_company:
                # Salvar dados da empresa selecionada na session_state
                st.session_state.selected_company_data = company_options[selected_company]
                
                # Mostrar dados da empresa selecionada
                st.write("**Empresa selecionada:**")
                for key, value in st.session_state.selected_company_data.items():
                    if key != 'id':
                        st.write(f"{key}: {value}")
        else:
            st.info("Nenhuma empresa cadastrada")
            
    except Exception as e:
        logger.error(f"Erro ao carregar empresas: {str(e)}")
        st.error("Erro ao carregar lista de empresas")

def get_openai_key():
    """Obtém a chave da API da OpenAI"""
    try:
        # Tentar ler a chave diretamente
        key = st.secrets.get("OPENAI_API_KEY")
        
        # Log para debug (não mostra a chave completa)
        if key:
            logger.info(f"Chave encontrada com tamanho: {len(key)}")
            logger.info(f"Primeiros caracteres: {key[:10]}")
        else:
            logger.error("Chave não encontrada em st.secrets")
            
        return key
        
    except Exception as e:
        logger.error(f"Erro ao obter chave da API: {str(e)}")
        raise Exception(f"Erro ao obter chave da API: {str(e)}")

def extract_flight_info(fatos_cliente):
    """Extrai informações do voo usando OpenAI"""
    try:
        api_key = get_openai_key()
        if not api_key:
            raise Exception("Chave da API não encontrada")
            
        client = OpenAI(
            api_key=api_key
        )
        
        # Teste simples antes de prosseguir
        test_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logger.info("Teste de conexão bem sucedido")
        
        system_prompt = """Você é um assistente especializado em extrair informações sobre problemas com voos. 
        Analise o texto fornecido e extraia as informações solicitadas.
        Responda APENAS com um JSON contendo os campos solicitados.
        Se alguma informação não estiver disponível no texto, use "Não informado"."""
        
        user_prompt = f"""Extraia as seguintes informações do texto abaixo:
        - motivo_voo: Motivo da viagem
        - problema: Qual foi o problema enfrentado
        - compromisso_perdido: Se perdeu algum compromisso por conta do atraso
        - contexto: Condição física ou emocional do passageiro
        - momento_informacao: Quando foi informado do problema
        - tipo_voo: Nacional ou Internacional
        - origem_voo: Cidade/Aeroporto de origem
        - destino_voo: Cidade/Aeroporto de destino
        - escala: Se houve e onde foi
        - local_problema: Onde ocorreu o problema
        - data_voo_inicial: Data prevista do voo
        - horario_voo_inicial: Horário previsto do voo
        - data_voo_real: Data em que o voo de fato aconteceu
        - horario_voo_real: Horário em que o voo de fato aconteceu
        - tempo_atraso: Tempo de atraso (calcule se possível)
        - solicitou_reacomodacao: Se solicitou ser reacomodado em outro voo
        - opcao_reacomodacao: Descreva a opção de reacomodação recebida
        - recebeu_auxilio: Se recebeu algum auxílio como voucher de hotel ou comida
        - auxilio_recebido: Descreva o auxílio recebido
        - teve_custos: Se teve algum custo com uber, hotel ou comida
        - descricao_custos: Descreva os custos
        - valor_total_custos: Valor total dos custos (danos materiais)

        Texto: {fatos_cliente}"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Converter a resposta para dict
            flight_info = json.loads(response.choices[0].message.content)
            return flight_info
            
        except Exception as e:
            logger.error(f"Erro na chamada da API OpenAI: {str(e)}")
            raise Exception("Erro ao processar o texto com a OpenAI. Por favor, tente novamente.")
            
    except Exception as e:
        logger.error(f"Erro ao processar texto com OpenAI: {str(e)}")
        raise e

def generate_facts_with_assistant(flight_info, fatos_cliente):
    """Gera os fatos formatados usando o OpenAI Assistant específico"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Usar o assistant específico
        assistant_id = "asst_Yjlfjp23PwM2qiN6ckjxUspB"
        
        # Criar um thread
        thread = client.beta.threads.create()
        
        # Preparar as informações do voo em um formato mais legível
        message_content = f"""
        FATOS RELATADOS PELO CLIENTE:
        {fatos_cliente}
        
        DADOS COMPLEMENTARES DO VOO:
        
        DADOS DO VOO:
        - Tipo: {flight_info['tipo_voo']}
        - Origem: {flight_info['origem_voo']}
        - Destino: {flight_info['destino_voo']}
        - Escala: {flight_info['escala']}
        - Data Prevista: {flight_info['data_voo_inicial']}
        - Horário Previsto: {flight_info['horario_voo_inicial']}
        - Data Real: {flight_info['data_voo_real']}
        - Horário Real: {flight_info['horario_voo_real']}
        - Tempo de Atraso: {flight_info['tempo_atraso']}
        
        DETALHES DO PROBLEMA:
        - Motivo da Viagem: {flight_info['motivo_voo']}
        - Problema: {flight_info['problema']}
        - Local do Problema: {flight_info['local_problema']}
        - Momento da Informação: {flight_info['momento_informacao']}
        - Compromisso Perdido: {flight_info['compromisso_perdido']}
        - Contexto do Passageiro: {flight_info['contexto']}
        
        AUXÍLIOS E CUSTOS:
        - Solicitou Reacomodação: {flight_info['solicitou_reacomodacao']}
        - Opção Recebida: {flight_info['opcao_reacomodacao']}
        - Recebeu Auxílio: {flight_info['recebeu_auxilio']}
        - Auxílio Recebido: {flight_info['auxilio_recebido']}
        - Teve Custos: {flight_info['teve_custos']}
        - Descrição dos Custos: {flight_info['descricao_custos']}
        - Valor Total: {flight_info['valor_total_custos']}
        """
        
        # Adicionar a mensagem ao thread
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Executar o assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        # Aguardar a conclusão
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                raise Exception("O assistente falhou ao processar a solicitação")
            elif run_status.status == 'expired':
                raise Exception("A solicitação expirou")
            time.sleep(1)
        
        # Obter a resposta
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value
        
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar fatos: {str(e)}")
        raise Exception(f"Erro ao gerar fatos: {str(e)}")

def render_facts_section():
    """Renderiza a seção de fatos do voo"""
    st.markdown("---")
    st.subheader("3. Fatos do Voo")
    
    audio_manager = AudioManager()
    
    # Botão para abrir o conversor de áudio online
    st.markdown("""
        <a href="https://online-audio-converter.com/pt/" target="_blank">
            <button style="
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 10px 24px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;">
                Converter Áudio
            </button>
        </a>
    """, unsafe_allow_html=True)
    
    st.write("") # Espaço entre os elementos
    
    # Upload do arquivo de áudio
    audio_file = st.file_uploader(
        "Fazer upload do áudio",
        type=['wav'],
        help="Por favor, envie o áudio no formato WAV"
    )
    
    if audio_file:
        # Salvar arquivo temporariamente
        audio_path = audio_manager.save_temp_audio(audio_file)
        
        # Botão para transcrever
        if st.button("Transcrever Áudio"):
            with st.spinner("Transcrevendo áudio..."):
                try:
                    transcription = audio_manager.transcribe_audio(audio_path)
                    st.session_state.transcription = transcription
                    st.session_state.last_text = transcription  # Guardar último texto processado
                except Exception as e:
                    logger.error(f"Erro na transcrição: {str(e)}")
                    st.error("Erro ao transcrever o áudio")
    
    # Campo editável com a transcrição
    fatos_cliente = st.text_area(
        "Fatos relatados pelo cliente",
        value=st.session_state.get('transcription', ''),
        height=300,
        key="fatos_cliente"
    )
    
    # Atualizar variável na session_state quando o texto for editado
    if fatos_cliente != st.session_state.get('transcription', ''):
        st.session_state.transcription = fatos_cliente
    
    # Botão para reconhecer informações
    if st.button("Reconhecer Informações", type="primary"):
        if not fatos_cliente:
            st.error("Por favor, forneça os fatos do voo antes de reconhecer as informações.")
            return
            
        try:
            with st.spinner("Analisando informações..."):
                flight_info = extract_flight_info(fatos_cliente)
                st.session_state.flight_info = flight_info
                st.success("Informações reconhecidas com sucesso!")
                st.rerun()  # Atualizar a página para mostrar as informações
        except Exception as e:
            st.error(f"Erro ao processar as informações: {str(e)}")
    
    # Inicializar flight_info se não existir
    if 'flight_info' not in st.session_state:
        st.session_state.flight_info = {
            'tipo_voo': '', 'origem_voo': '', 'destino_voo': '', 'escala': '',
            'data_voo_inicial': '', 'horario_voo_inicial': '', 'data_voo_real': '',
            'horario_voo_real': '', 'tempo_atraso': '', 'motivo_voo': '',
            'problema': '', 'local_problema': '', 'momento_informacao': '',
            'compromisso_perdido': '', 'contexto': '', 'solicitou_reacomodacao': '',
            'opcao_reacomodacao': '', 'recebeu_auxilio': '', 'auxilio_recebido': '',
            'teve_custos': '', 'descricao_custos': '', 'valor_total_custos': ''
        }
    
    # Mostrar campos editáveis
    st.subheader("Informações do Voo:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Dados do Voo:**")
        st.session_state.flight_info['tipo_voo'] = st.text_input(
            "Tipo de Voo", 
            value=st.session_state.flight_info.get('tipo_voo', '')
        )
        st.session_state.flight_info['origem_voo'] = st.text_input(
            "Origem", 
            value=st.session_state.flight_info.get('origem_voo', '')
        )
        st.session_state.flight_info['destino_voo'] = st.text_input(
            "Destino", 
            value=st.session_state.flight_info.get('destino_voo', '')
        )
        st.session_state.flight_info['escala'] = st.text_input(
            "Escala", 
            value=st.session_state.flight_info.get('escala', '')
        )
        
        # Campo de data prevista
        try:
            data_prevista = st.date_input(
                "Data Prevista",
                value=None if not st.session_state.flight_info.get('data_voo_inicial') or 
                          st.session_state.flight_info['data_voo_inicial'] == "Não informado" or
                          format_date(st.session_state.flight_info['data_voo_inicial']) == ""
                else datetime.strptime(format_date(st.session_state.flight_info['data_voo_inicial']), "%d/%m/%Y"),
                format="DD/MM/YYYY"
            )
            st.session_state.flight_info['data_voo_inicial'] = data_prevista.strftime("%d/%m/%Y") if data_prevista else ""
        except:
            data_prevista = st.date_input("Data Prevista", value=None, format="DD/MM/YYYY")
            st.session_state.flight_info['data_voo_inicial'] = data_prevista.strftime("%d/%m/%Y") if data_prevista else ""
        
        # Campo de horário previsto
        try:
            horario_previsto = st.time_input(
                "Horário Previsto",
                value=None if not st.session_state.flight_info.get('horario_voo_inicial') or
                          st.session_state.flight_info['horario_voo_inicial'] == "Não informado" or
                          format_time(st.session_state.flight_info['horario_voo_inicial']) == ""
                else datetime.strptime(format_time(st.session_state.flight_info['horario_voo_inicial']), "%H:%M").time()
            )
            st.session_state.flight_info['horario_voo_inicial'] = horario_previsto.strftime("%H:%M") if horario_previsto else ""
        except:
            horario_previsto = st.time_input("Horário Previsto", value=None)
            st.session_state.flight_info['horario_voo_inicial'] = horario_previsto.strftime("%H:%M") if horario_previsto else ""
        
        # Campo de data real
        try:
            data_real = st.date_input(
                "Data Real",
                value=None if not st.session_state.flight_info.get('data_voo_real') or
                          st.session_state.flight_info['data_voo_real'] == "Não informado" or
                          format_date(st.session_state.flight_info['data_voo_real']) == ""
                else datetime.strptime(format_date(st.session_state.flight_info['data_voo_real']), "%d/%m/%Y"),
                format="DD/MM/YYYY"
            )
            st.session_state.flight_info['data_voo_real'] = data_real.strftime("%d/%m/%Y") if data_real else ""
        except:
            data_real = st.date_input("Data Real", value=None, format="DD/MM/YYYY")
            st.session_state.flight_info['data_voo_real'] = data_real.strftime("%d/%m/%Y") if data_real else ""
        
        # Campo de horário real
        try:
            horario_real = st.time_input(
                "Horário Real",
                value=None if not st.session_state.flight_info.get('horario_voo_real') or
                          st.session_state.flight_info['horario_voo_real'] == "Não informado" or
                          format_time(st.session_state.flight_info['horario_voo_real']) == ""
                else datetime.strptime(format_time(st.session_state.flight_info['horario_voo_real']), "%H:%M").time()
            )
            st.session_state.flight_info['horario_voo_real'] = horario_real.strftime("%H:%M") if horario_real else ""
        except:
            horario_real = st.time_input("Horário Real", value=None)
            st.session_state.flight_info['horario_voo_real'] = horario_real.strftime("%H:%M") if horario_real else ""
        
        st.session_state.flight_info['tempo_atraso'] = st.text_input(
            "Tempo de Atraso", 
            value=st.session_state.flight_info.get('tempo_atraso', '')
        )
    
    with col2:
        st.write("**Detalhes do Problema:**")
        st.session_state.flight_info['motivo_voo'] = st.text_input(
            "Motivo da Viagem", 
            value=st.session_state.flight_info.get('motivo_voo', '')
        )
        st.session_state.flight_info['problema'] = st.text_area(
            "Problema Enfrentado", 
            value=st.session_state.flight_info.get('problema', ''),
            height=100
        )
        st.session_state.flight_info['local_problema'] = st.text_input(
            "Local do Problema", 
            value=st.session_state.flight_info.get('local_problema', '')
        )
        st.session_state.flight_info['momento_informacao'] = st.text_input(
            "Momento da Informação", 
            value=st.session_state.flight_info.get('momento_informacao', '')
        )
        st.session_state.flight_info['compromisso_perdido'] = st.text_area(
            "Compromisso Perdido", 
            value=st.session_state.flight_info.get('compromisso_perdido', ''),
            height=100
        )
        st.session_state.flight_info['contexto'] = st.text_area(
            "Contexto do Passageiro", 
            value=st.session_state.flight_info.get('contexto', ''),
            height=100
        )
    
    with col3:
        st.write("**Auxílios e Custos:**")
        st.session_state.flight_info['solicitou_reacomodacao'] = st.text_input(
            "Solicitou Reacomodação?", 
            value=st.session_state.flight_info.get('solicitou_reacomodacao', '')
        )
        st.session_state.flight_info['opcao_reacomodacao'] = st.text_area(
            "Opção de Reacomodação Recebida", 
            value=st.session_state.flight_info.get('opcao_reacomodacao', ''),
            height=100
        )
        st.session_state.flight_info['recebeu_auxilio'] = st.text_input(
            "Recebeu Auxílio?", 
            value=st.session_state.flight_info.get('recebeu_auxilio', '')
        )
        st.session_state.flight_info['auxilio_recebido'] = st.text_area(
            "Auxílio Recebido", 
            value=st.session_state.flight_info.get('auxilio_recebido', ''),
            height=100
        )
        st.session_state.flight_info['teve_custos'] = st.text_input(
            "Teve Custos Extras?", 
            value=st.session_state.flight_info.get('teve_custos', '')
        )
        st.session_state.flight_info['descricao_custos'] = st.text_area(
            "Descrição dos Custos", 
            value=st.session_state.flight_info.get('descricao_custos', ''),
            height=100
        )
        st.session_state.flight_info['valor_total_custos'] = st.text_input(
            "Valor Total dos Custos", 
            value=st.session_state.flight_info.get('valor_total_custos', '')
        )
    
    # Seção de Geração de Fatos
    st.markdown("---")
    
    # Verificar se todos os dados necessários estão presentes
    if st.button("Gerar Fatos", type="primary"):
        if not fatos_cliente:
            st.error("Por favor, preencha os fatos relatados pelo cliente antes de gerar os fatos.")
            return
            
        if not hasattr(st.session_state, 'flight_info'):
            st.error("Por favor, preencha as informações do voo antes de gerar os fatos.")
            return
            
        try:
            with st.spinner("Gerando fatos do caso..."):
                generated_facts = generate_facts_with_assistant(
                    st.session_state.flight_info,
                    fatos_cliente
                )
                st.session_state.generated_facts = generated_facts
                st.success("Fatos gerados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao gerar fatos: {str(e)}")
            if st.button("Tentar Novamente"):
                st.rerun()
    
    # Mostrar os fatos gerados em uma caixa editável se existirem
    if 'generated_facts' in st.session_state:
        st.markdown("### Fatos Gerados")
        st.markdown("_Você pode editar o texto abaixo se necessário:_")
        edited_facts = st.text_area(
            "Fatos do Caso",
            value=st.session_state.generated_facts,
            height=400,
            key="facts_text_area"
        )
        
        # Salvar os fatos editados na session_state
        if edited_facts != st.session_state.generated_facts:
            st.session_state.generated_facts = edited_facts
            st.info("As alterações foram salvas!")
    
    # Botões de ação (sempre visíveis)
    st.markdown("### Ações")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Botão Gerar Novamente
        if st.button("Gerar Novamente", type="primary", use_container_width=True, key="btn_gerar"):
            if not fatos_cliente:
                st.error("Por favor, preencha os fatos relatados pelo cliente antes de gerar os fatos.")
                return
            
            if not hasattr(st.session_state, 'flight_info'):
                st.error("Por favor, preencha as informações do voo antes de gerar os fatos.")
                return
            
            try:
                with st.spinner("Gerando novos fatos..."):
                    generated_facts = generate_facts_with_assistant(
                        st.session_state.flight_info,
                        fatos_cliente
                    )
                    st.session_state.generated_facts = generated_facts
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar novos fatos: {str(e)}")
        
        # Botão Salvar para Treinamento
        if st.button("Salvar para Treinamento", type="primary", use_container_width=True, key="btn_salvar"):
            if not hasattr(st.session_state, 'generated_facts'):
                st.error("Por favor, gere os fatos antes de salvar para treinamento.")
                return
                
            try:
                supabase = SupabaseManager()
                caso = st.session_state.selected_case_data.get('assunto_caso', 'Não informado')
                
                # Recriar o message_content
                message_content = f"""
                FATOS RELATADOS PELO CLIENTE:
                {fatos_cliente}
                
                DADOS COMPLEMENTARES DO VOO:
                
                DADOS DO VOO:
                - Tipo: {st.session_state.flight_info['tipo_voo']}
                - Origem: {st.session_state.flight_info['origem_voo']}
                - Destino: {st.session_state.flight_info['destino_voo']}
                - Escala: {st.session_state.flight_info['escala']}
                - Data Prevista: {st.session_state.flight_info['data_voo_inicial']}
                - Horário Previsto: {st.session_state.flight_info['horario_voo_inicial']}
                - Data Real: {st.session_state.flight_info['data_voo_real']}
                - Horário Real: {st.session_state.flight_info['horario_voo_real']}
                - Tempo de Atraso: {st.session_state.flight_info['tempo_atraso']}
                
                DETALHES DO PROBLEMA:
                - Motivo da Viagem: {st.session_state.flight_info['motivo_voo']}
                - Problema: {st.session_state.flight_info['problema']}
                - Local do Problema: {st.session_state.flight_info['local_problema']}
                - Momento da Informação: {st.session_state.flight_info['momento_informacao']}
                - Compromisso Perdido: {st.session_state.flight_info['compromisso_perdido']}
                - Contexto do Passageiro: {st.session_state.flight_info['contexto']}
                
                AUXÍLIOS E CUSTOS:
                - Solicitou Reacomodação: {st.session_state.flight_info['solicitou_reacomodacao']}
                - Opção Recebida: {st.session_state.flight_info['opcao_reacomodacao']}
                - Recebeu Auxílio: {st.session_state.flight_info['recebeu_auxilio']}
                - Auxílio Recebido: {st.session_state.flight_info['auxilio_recebido']}
                - Teve Custos: {st.session_state.flight_info['teve_custos']}
                - Descrição dos Custos: {st.session_state.flight_info['descricao_custos']}
                - Valor Total: {st.session_state.flight_info['valor_total_custos']}
                """
                
                # Salvar no banco de dados
                supabase.save_facts_for_training(
                    caso=caso,
                    input_text=message_content,
                    output_text=st.session_state.generated_facts
                )
                
                st.success("Fatos salvos para treinamento com sucesso!")
                
            except Exception as e:
                st.error(f"Erro ao salvar para treinamento: {str(e)}")
    
    st.markdown("---")

    # Seção de Petição Inicial
    st.markdown("### Petição Inicial")
    
    # 1. Qualificação das Partes
    st.markdown("#### 1. Qualificação das Partes")
    
    # Campo para Vara Cível
    vara_civil = st.text_input("Vara Cível", key="vara_civil")
    
    # Verificar se temos os dados do cliente e da empresa
    if hasattr(st.session_state, 'selected_client_data') and hasattr(st.session_state, 'selected_company_data'):
        client_data = st.session_state.selected_client_data
        company_data = st.session_state.selected_company_data
        
        # Campo de texto para qualificação do cliente
        client_text = f"""{vara_civil}

{client_data.get('nome_completo', '')}, \
{client_data.get('nacionalidade', 'brasileiro(a)')}, \
{client_data.get('estado_civil', '')}, \
{client_data.get('profissao', '')}, \
portador da carteira de identidade nº {client_data.get('rg', '')} \
expedida pelo {client_data.get('orgao_emissor', '')}, \
inscrito no CPF nº {client_data.get('cpf', '')}, \
residente e domiciliado na {client_data.get('endereco', '')}, \
CEP: {client_data.get('cep', '')}, \
endereço eletrônico contato@smartlegabr.com, \
por meio de seus advogados que a esta subscrevem, \
com escritório na Rua Siqueira Campos, nº 243, salas 703, Copacabana, \
Rio de Janeiro – RJ, CEP: 22.031-071, onde recebem intimações \
com fulcro nos arts. 5º, inciso V da Constituição Federal c/c arts. 186 e 927 do Código Civil, \
vem, respeitosamente propor a presente"""

        st.text_area(
            "Qualificação Cliente",
            value=client_text,
            height=200,
            key="client_qualification"
        )
        
        # Título da Ação
        st.markdown("#### AÇÃO INDENIZATÓRIA POR DANOS MORAIS E MATERIAIS")
        
        # Campo de texto para qualificação da empresa
        company_text = f"""em face de {company_data.get('nome', '')}, \
pessoa jurídica de direito privado, \
inscrita no CNPJ sob o nº {company_data.get('cnpj', '')}, \
estabelecida à {company_data.get('endereco', '')}, \
pelos fatos e fundamentos a seguir expostos."""

        st.text_area(
            "Qualificação Empresa",
            value=company_text,
            height=150,
            key="company_qualification"
        )
        
        # Título e texto das publicações
        st.markdown("**DAS PUBLICAÇÕES**")
        publications_text = """Quanto às publicações, requer seja anotado na capa destes autos o nome do advogado Dr. Marcelo Victor Pereira Nunes Cavalcante, inscrito na OAB/RJ-246336, para recebimento de todas as publicações oficiais, sob pena de nulidade, na forma do §2º do artigo 272 do CPC."""
        
        st.text_area(
            "Das Publicações",
            value=publications_text,
            height=150,
            key="publications_text"
        )
    else:
        st.warning("Por favor, selecione um cliente e uma empresa aérea para gerar a qualificação.")
    
    st.markdown("---")
    
    # Dos Fatos
    st.markdown("#### 2. Dos Fatos")
    if 'generated_facts' in st.session_state:
        st.text_area(
            "Narrativa dos Fatos",
            value=st.session_state.generated_facts,
            height=300,
            key="narrative_facts"
        )
    
    st.markdown("---")
    
    # Do Direito
    st.markdown("#### 3. Do Direito")
    
    # 3.1 - Título fixo
    st.markdown("""
    ##### 3.1 - DOS DEVERES DO TRANSPORTADOR EM DECORRÊNCIA DA FALHA NA PRESTAÇÃO DA INFORMAÇÃO – INOBSERVÂNCIA DO ART. 12 CAPUT DA RESOLUÇÃO Nº 400/2016 DA ANAC.
    """)
    
    # Texto editável sobre os deveres do transportador
    legal_text_1 = st.text_area(
        "Fundamentação",
        value="""Consoante o exposto na narrativa dos fatos, observamos o tratamento reprovável que a empresa Ré apresentou ao Autor, se eximindo da responsabilidade de prestar todas as informações concernentes ao voo.

No que tange ao dever do transportador em prestar informações aos consumidores, a resolução nº 400 da ANAC buscou de forma prática amparar o usuário quanto ao seu direito de informação. Conforme aduz o art. 12:

Art. 12. As alterações realizadas de forma programada pelo transportador, em especial quanto ao horário e itinerário originalmente contratados, deverão ser informadas aos passageiros com antecedência mínima de 72 (setenta e duas) horas.

O prazo do transportador aéreo para informar ao consumidor sobre o cancelamento e/ou alteração do voo é de 72 horas, especialmente no que tange ao itinerário e horário.""",
        height=300,
        key="legal_text_1"
    )
    
    # Separador para a próxima subseção
    st.markdown("---")
    
    # Dos Pedidos
    st.markdown("#### 4. Dos Pedidos")
    if st.button("Gerar Pedidos", type="primary", use_container_width=True):
        st.info("Em desenvolvimento: Geração automática dos pedidos")
    
    # Campo para exibir/editar os pedidos
    st.text_area(
        "Pedidos",
        value="",  # Aqui virá o texto gerado pelo assistant
        height=300,
        key="requests"
    )
    
    st.markdown("---")
    
    # Botão para gerar a petição completa
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Gerar Petição Completa", type="primary", use_container_width=True):
            st.info("Em desenvolvimento: Geração da petição inicial completa")
    
    st.markdown("---")

def format_date(date_str):
    """Converte a data para o formato dd/mm/aaaa"""
    if not date_str or date_str == "Não informado":
        return ""
    try:
        # Remover possíveis textos extras
        date_str = date_str.lower().replace(" de ", "/")
        
        # Converter nomes dos meses para números
        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
            'marco': '03'  # Versão sem acento
        }
        
        for mes, num in meses.items():
            date_str = date_str.replace(mes, num)
        
        # Tentar diferentes formatos de entrada
        formatos = [
            "%d/%m/%Y",  # 31/12/2023
            "%Y-%m-%d",  # 2023-12-31
            "%d-%m-%Y",  # 31-12-2023
            "%d/%m/%y",  # 31/12/23
            "%d %m %Y",  # 31 12 2023
        ]
        
        for fmt in formatos:
            try:
                return datetime.strptime(date_str, fmt).strftime("%d/%m/%Y")
            except:
                continue
                
        # Se nenhum formato funcionar, tentar extrair os números
        import re
        numeros = re.findall(r'\d+', date_str)
        if len(numeros) >= 3:
            dia = numeros[0].zfill(2)
            mes = numeros[1].zfill(2)
            ano = numeros[2]
            if len(ano) == 2:
                ano = '20' + ano
            return f"{dia}/{mes}/{ano}"
            
        return ""
    except:
        return ""

def format_time(time_str):
    """Converte a hora para o formato HH:MM"""
    if not time_str or time_str == "Não informado":
        return ""
    try:
        # Remover possíveis textos extras
        time_str = time_str.lower().replace('h', ':').replace('hrs', ':00')
        
        # Tentar diferentes formatos de entrada
        formatos = [
            "%H:%M",     # 14:30
            "%H:%M:%S",  # 14:30:00
            "%I:%M %p",  # 02:30 PM
            "%H",        # 14
        ]
        
        for fmt in formatos:
            try:
                return datetime.strptime(time_str, fmt).strftime("%H:%M")
            except:
                continue
                
        # Se nenhum formato funcionar, tentar extrair os números
        import re
        numeros = re.findall(r'\d+', time_str)
        if len(numeros) >= 1:
            hora = numeros[0].zfill(2)
            minuto = numeros[1].zfill(2) if len(numeros) > 1 else "00"
            return f"{hora}:{minuto}"
            
        return ""
    except:
        return ""

def render_atraso_voo():
    """Renderiza a página de Atraso/Cancelamento de Voo"""
    st.title("Atraso / Cancelamento de Voo")
    
    # Renderizar cada seção
    render_client_section()
    render_company_section()
    render_facts_section() 