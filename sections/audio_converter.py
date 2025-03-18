import streamlit as st
from pydub import AudioSegment
import os
import tempfile
from datetime import datetime
import logging
import subprocess

logger = logging.getLogger(__name__)

def check_ffmpeg():
    """Verifica se o FFmpeg está instalado e configurado"""
    try:
        # Tenta executar ffmpeg
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_ffmpeg():
    """Configura o caminho do FFmpeg para o pydub"""
    try:
        # No Linux (Streamlit Cloud), o ffmpeg geralmente está em /usr/bin/ffmpeg
        if os.path.exists('/usr/bin/ffmpeg'):
            AudioSegment.converter = '/usr/bin/ffmpeg'
            return True
        # No Windows, procura no PATH
        elif os.name == 'nt':
            windows_paths = [
                'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
                'C:\\ffmpeg\\bin\\ffmpeg.exe',
                os.path.join(os.environ.get('USERPROFILE', ''), 'ffmpeg', 'bin', 'ffmpeg.exe')
            ]
            for path in windows_paths:
                if os.path.exists(path):
                    AudioSegment.converter = path
                    return True
        return False
    except Exception as e:
        logger.error(f"Erro ao configurar FFmpeg: {str(e)}")
        return False

def convert_audio(input_file, output_format):
    """Converte o arquivo de áudio para o formato especificado"""
    # Verificar e configurar FFmpeg
    if not check_ffmpeg():
        if not setup_ffmpeg():
            raise Exception(
                "FFmpeg não encontrado. Este componente é necessário para a conversão de áudio. "
                "Por favor, certifique-se de que o FFmpeg está instalado no sistema."
            )
    
    try:
        # Criar diretório temporário
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar arquivo de entrada
        input_path = os.path.join(temp_dir, f"input_{timestamp}{os.path.splitext(input_file.name)[1]}")
        with open(input_path, "wb") as f:
            f.write(input_file.getbuffer())
        
        try:
            # Carregar áudio com pydub
            if input_file.type == 'audio/ogg' or input_file.type == 'application/ogg':
                audio = AudioSegment.from_ogg(input_path)
            elif input_file.type == 'audio/mpeg':
                audio = AudioSegment.from_mp3(input_path)
            elif input_file.type == 'audio/wav':
                audio = AudioSegment.from_wav(input_path)
            elif input_file.type in ['audio/x-m4a', 'audio/mp4']:
                audio = AudioSegment.from_file(input_path, format='m4a')
            else:
                audio = AudioSegment.from_file(input_path)
            
        except FileNotFoundError:
            raise Exception(
                "FFmpeg não encontrado ou não está funcionando corretamente. "
                "Por favor, tente novamente em alguns instantes."
            )
        except Exception as e:
            raise Exception(f"Erro ao processar o arquivo de áudio: {str(e)}")
        
        # Criar nome para arquivo de saída
        output_path = os.path.join(temp_dir, f"output_{timestamp}.{output_format}")
        
        # Converter e exportar
        audio.export(output_path, format=output_format)
        
        # Ler arquivo convertido
        with open(output_path, "rb") as f:
            converted_data = f.read()
        
        # Limpar arquivos temporários
        try:
            os.remove(input_path)
            os.remove(output_path)
        except:
            pass  # Ignora erros na limpeza de arquivos temporários
        
        return converted_data
        
    except Exception as e:
        logger.error(f"Erro na conversão do áudio: {str(e)}")
        # Tentar limpar arquivos temporários em caso de erro
        try:
            if 'input_path' in locals():
                os.remove(input_path)
            if 'output_path' in locals():
                os.remove(output_path)
        except:
            pass
        raise e

def render_audio_converter():
    """Renderiza a página de conversão de áudio"""
    st.title("Conversão de Áudio")
    
    st.write("""
    Esta ferramenta permite converter arquivos de áudio para o formato WAV.
    Útil para converter áudios do WhatsApp (OGG) para WAV, que é necessário para a transcrição.
    """)
    
    # Upload do arquivo
    input_file = st.file_uploader(
        "Selecione o arquivo de áudio",
        type=['ogg', 'mp3', 'wav', 'm4a', 'mp4', 'oga'],
        help="Formatos suportados: OGG (WhatsApp), MP3, WAV, M4A, MP4"
    )
    
    if input_file:
        st.write("")  # Espaço entre o upload e o botão
        
        # Botão de conversão
        if st.button("Converter para WAV"):
            try:
                with st.spinner("Convertendo arquivo..."):
                    converted_data = convert_audio(input_file, 'wav')
                
                # Oferecer o download do arquivo convertido
                st.download_button(
                    label="Baixar arquivo WAV",
                    data=converted_data,
                    file_name=f"convertido.wav",
                    mime="audio/wav"
                )
                
                st.success("Conversão concluída!")
                
            except Exception as e:
                st.error(str(e))
                logger.error(f"Erro detalhado: {str(e)}") 