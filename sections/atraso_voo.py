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

def generate_facts_with_assistant(flight_info):
    """Gera os fatos formatados usando o OpenAI Assistant"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Criar um assistant temporário
        assistant = client.beta.assistants.create(
            name="Gerador de Fatos",
            instructions="""Você é um especialista em direito do consumidor, 
            especializado em casos de atrasos e cancelamentos de voos. 
            Sua tarefa é gerar um texto bem formatado descrevendo os fatos do caso,
            usando as informações fornecidas para criar uma narrativa clara e objetiva.
            Use parágrafos bem estruturados e mantenha um tom profissional.""",
            model="gpt-4-turbo-preview"
        )
        
        # Criar um thread
        thread = client.beta.threads.create()
        
        # Preparar as informações do voo em um formato mais legível
        message_content = f"""
        Por favor, gere um texto descrevendo os fatos deste caso usando as seguintes informações:
        
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
            assistant_id=assistant.id
        )
        
        # Aguardar a conclusão
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            time.sleep(1)
        
        # Obter a resposta
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value
        
        # Limpar recursos
        client.beta.assistants.delete(assistant.id)
        
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
    if st.button("Gerar Fatos", type="primary"):
        try:
            with st.spinner("Gerando fatos do caso..."):
                generated_facts = generate_facts_with_assistant(st.session_state.flight_info)
                st.session_state.generated_facts = generated_facts
                st.success("Fatos gerados com sucesso!")
        except Exception as e:
            st.error(str(e))
    
    # Mostrar os fatos gerados em uma caixa editável
    if 'generated_facts' in st.session_state:
        st.text_area(
            "Fatos do Caso",
            value=st.session_state.generated_facts,
            height=400,
            key="facts_text_area"
        )
        st.markdown("---")  # Adiciona um separador após os fatos

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