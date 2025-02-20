import json
from typing import List, Dict, Any, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from config.settings import (
    GOOGLE_CREDENTIALS,
    SHEETS_SCOPE,
    DRIVE_SCOPE,
    DOCS_SCOPE,
    SHEET_ID_1,
    SHEET_ID_2,
    ROOT_FOLDER_ID
)
from utils.date_utils import data_por_extenso
from utils.error_handler import DriveError
from datetime import datetime
from docx import Document
import re
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

logger.info(f"Diretório atual: {os.getcwd()}")

class GoogleManager:
    def __init__(self):
        self.credentials = self._get_credentials()
        self.sheets_service = self._build_sheets_service()
        self.drive_service = self._build_drive_service()
        self.docs_service = self._build_docs_service()

    def _get_credentials(self):
        """Cria credenciais do Google a partir do JSON armazenado"""
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scopes = SHEETS_SCOPE + DRIVE_SCOPE + DOCS_SCOPE
        return service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )

    def _build_sheets_service(self):
        """Cria serviço do Google Sheets"""
        return build('sheets', 'v4', credentials=self.credentials)

    def _build_drive_service(self):
        """Cria serviço do Google Drive"""
        return build('drive', 'v3', credentials=self.credentials)

    def _build_docs_service(self):
        """Cria serviço do Google Docs"""
        return build('docs', 'v1', credentials=self.credentials)

    def update_sheet(self, sheet_id: str, range_name: str, values: List[List[Any]]):
        """Adiciona dados na última linha da planilha do Google Sheets"""
        try:
            # Primeiro, encontra a última linha com dados
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            # Pega o número da próxima linha vazia
            last_row = len(result.get('values', [])) + 1
            
            # Ajusta o range para apontar para a próxima linha vazia
            column_range = range_name.split(':')[1]
            new_range = f"A{last_row}:{column_range}{last_row}"
            
            # Faz o append dos dados
            body = {'values': values}
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range=new_range,
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Dados adicionados na linha {last_row} da planilha {sheet_id}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar planilha: {str(e)}")
            raise Exception(f"Erro ao atualizar planilha: {str(e)}")

    def create_folder(self, folder_name: str, parent_id: str = ROOT_FOLDER_ID) -> str:
        """Cria uma pasta no Google Drive"""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            file = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            raise Exception(f"Erro ao criar pasta: {str(e)}")

    def upload_file(self, file_name: str, file_content: bytes, mime_type: str, folder_id: str) -> str:
        """Faz upload de um arquivo para o Google Drive"""
        try:
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            media = MediaIoBaseUpload(
                BytesIO(file_content),
                mimetype=mime_type,
                resumable=True
            )
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            return file.get('id')
        except Exception as e:
            raise Exception(f"Erro ao fazer upload do arquivo: {str(e)}")

    def fill_document_template(self, template_path: str, data: Dict[str, str], folder_id: str) -> Tuple[str, str]:
        """
        Preenche o template e salva como PDF e DOCX
        Retorna: (pdf_id, docx_id)
        """
        try:
            # Verifica se o arquivo existe (usando caminho absoluto)
            template_full_path = os.path.join(os.getcwd(), 'templates', template_path)
            if not os.path.exists(template_full_path):
                raise DriveError(f"Template não encontrado: {template_full_path}")
            
            logger.info(f"Usando template em: {template_full_path}")

            # Carrega o template
            try:
                doc = Document(template_full_path)
            except Exception as e:
                raise DriveError(f"Erro ao carregar template: {str(e)}")
            
            # Log dos dados
            logger.info(f"Dados para substituição: {data}")
            
            # Substitui os placeholders em todo o documento
            for paragraph in doc.paragraphs:
                original_text = paragraph.text
                for key, value in data.items():
                    if f"{{{{{key}}}}}" in paragraph.text:
                        paragraph.text = paragraph.text.replace(f"{{{{{key}}}}}", str(value))
                logger.debug(f"Texto original: {original_text}")
                logger.debug(f"Texto substituído: {paragraph.text}")
            
            # Salva o documento temporariamente
            temp_docx = BytesIO()
            try:
                doc.save(temp_docx)
                temp_docx.seek(0)
            except Exception as e:
                raise DriveError(f"Erro ao salvar documento temporário: {str(e)}")
            
            # Upload do DOCX
            try:
                docx_id = self.upload_file(
                    f'Procuracao_{data["nome_completo"]}.docx',
                    temp_docx.getvalue(),
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    folder_id
                )
                logger.info(f"DOCX criado com ID: {docx_id}")
            except Exception as e:
                raise DriveError(f"Erro ao fazer upload do DOCX: {str(e)}")
            
            # Converte para Google Docs temporariamente para gerar PDF
            try:
                file_metadata = {
                    'name': 'temp_doc',
                    'mimeType': 'application/vnd.google-apps.document',
                    'parents': [folder_id]
                }
                
                media = MediaIoBaseUpload(
                    temp_docx,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    resumable=True
                )
                
                temp_doc = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                logger.info(f"Documento temporário criado com ID: {temp_doc['id']}")
            except Exception as e:
                raise DriveError(f"Erro ao criar documento temporário: {str(e)}")
            
            # Exporta como PDF
            try:
                pdf_content = self.export_to_pdf(temp_doc['id'])
                pdf_id = self.upload_file(
                    f'Procuracao_{data["nome_completo"]}.pdf',
                    pdf_content,
                    'application/pdf',
                    folder_id
                )
                logger.info(f"PDF criado com ID: {pdf_id}")
            except Exception as e:
                raise DriveError(f"Erro ao gerar PDF: {str(e)}")
            
            # Remove o documento temporário
            try:
                self.drive_service.files().delete(fileId=temp_doc['id']).execute()
                logger.info("Documento temporário removido")
            except Exception as e:
                logger.warning(f"Erro ao remover documento temporário: {str(e)}")
            
            return pdf_id, docx_id
            
        except Exception as e:
            logger.error(f"Erro ao processar template: {str(e)}")
            raise DriveError(f"Erro ao processar template: {str(e)}")

    def export_to_pdf(self, doc_id: str) -> bytes:
        """Exporta um documento do Google Docs para PDF"""
        try:
            return self.drive_service.files().export(
                fileId=doc_id,
                mimeType='application/pdf'
            ).execute()
        except Exception as e:
            raise Exception(f"Erro ao exportar para PDF: {str(e)}")

    def update_sheets_with_client_data(self, client_data: Dict[str, Any], folder_url: str):
        """Atualiza as duas planilhas com os dados do cliente"""
        try:
            # Formata a data de nascimento
            data_nascimento = datetime.fromisoformat(client_data['data_nascimento'])
            data_nascimento_formatada = data_nascimento.strftime('%d/%m/%Y')
            
            # Atualiza primeira planilha (todos os dados)
            values1 = [[
                client_data['nome_completo'],
                client_data['nacionalidade'],
                client_data['estado_civil'],
                client_data['profissao'],
                client_data['email'],
                client_data['celular'],
                data_nascimento_formatada,  # Data formatada
                client_data['rg'],
                client_data['cpf'],
                client_data['caso'],
                client_data['assunto_caso'],
                client_data['responsavel_comercial'],
                client_data['endereco'],
                client_data['bairro'],
                client_data['cidade'],
                client_data['estado'],
                client_data['cep'],
                folder_url
            ]]
            
            # Append direto na primeira planilha
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID_1,
                range='A:R',  # Ajustado para incluir a coluna do link
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': values1}
            ).execute()
            logger.info(f"Planilha 1 atualizada com dados de {client_data['nome_completo']}")
            
            # Atualiza segunda planilha (dados específicos)
            current_date = datetime.now().strftime('%d/%m/%Y')
            values2 = [[
                client_data['nome_completo'],      # A: Cliente
                current_date,                      # B: Data Entrada
                client_data['responsavel_comercial'], # C: Responsavel Comercial
                client_data['caso'],              # D: Caso
                client_data['assunto_caso'],      # E: Assunto Caso
                "",                               # F: Quem está fazendo (vazio)
                "Em andamento",                   # G: Status
                "",                               # H: Data Audiencia (vazio)
                folder_url                        # I: Pasta Drive
            ]]
            
            # Append direto na segunda planilha
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SHEET_ID_2,
                range='A:I',  # Ajustado para incluir todas as colunas
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body={'values': values2}
            ).execute()
            logger.info(f"Planilha 2 atualizada com dados de {client_data['nome_completo']}")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar planilhas: {str(e)}")
            raise Exception(f"Erro ao atualizar planilhas: {str(e)}") 