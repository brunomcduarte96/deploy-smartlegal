import streamlit as st
import os
import tempfile
import logging
from datetime import datetime
import speech_recognition as sr

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.recognizer = sr.Recognizer()
    
    def save_temp_audio(self, audio_file):
        """Salva o arquivo de áudio temporariamente"""
        try:
            # Criar nome único para o arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(self.temp_dir, f"audio_{timestamp}.wav")
            
            # Salvar arquivo
            with open(temp_path, "wb") as f:
                f.write(audio_file.getbuffer())
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar áudio: {str(e)}")
            raise e
    
    def transcribe_audio(self, audio_path):
        """Transcreve o áudio para texto usando Google Speech Recognition"""
        try:
            # Carregar o arquivo de áudio
            with sr.AudioFile(audio_path) as source:
                # Ajustar para ruído ambiente
                self.recognizer.adjust_for_ambient_noise(source)
                # Capturar o áudio
                audio = self.recognizer.record(source)
                
                # Realizar o reconhecimento
                text = self.recognizer.recognize_google(
                    audio,
                    language='pt-BR'  # Definir português do Brasil
                )
                
                # Limpar arquivo temporário
                try:
                    os.remove(audio_path)
                except:
                    pass
                
                return text
            
        except sr.UnknownValueError:
            raise Exception("Não foi possível entender o áudio")
        except sr.RequestError as e:
            raise Exception(f"Erro na requisição ao serviço de reconhecimento: {str(e)}")
        except Exception as e:
            logger.error(f"Erro na transcrição: {str(e)}")
            raise e 