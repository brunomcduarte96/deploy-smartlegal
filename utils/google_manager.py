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
from datetime import datetime

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
        """Atualiza dados em uma planilha do Google Sheets"""
        try:
            body = {'values': values}
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
        except Exception as e:
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
            # Carrega o template
            with open(template_path, 'rb') as doc:
                doc_content = doc.read()
            
            # Upload do template para o Drive
            temp_doc_id = self.upload_file(
                "temp_template.docx",
                doc_content,
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                folder_id
            )
            
            # Prepara as substituições
            requests = []
            for key, value in data.items():
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': f'{{{{{key}}}}}',
                            'matchCase': True
                        },
                        'replaceText': value
                    }
                })
            
            # Aplica as substituições
            self.docs_service.documents().batchUpdate(
                documentId=temp_doc_id,
                body={'requests': requests}
            ).execute()
            
            # Salva como DOCX
            docx_id = self.drive_service.files().copy(
                fileId=temp_doc_id,
                body={'name': f'Procuracao_{data["nome_completo"]}.docx'}
            ).execute()['id']
            
            # Exporta como PDF
            pdf_content = self.export_to_pdf(temp_doc_id)
            pdf_id = self.upload_file(
                f'Procuracao_{data["nome_completo"]}.pdf',
                pdf_content,
                'application/pdf',
                folder_id
            )
            
            # Remove o arquivo temporário
            self.drive_service.files().delete(fileId=temp_doc_id).execute()
            
            return pdf_id, docx_id
            
        except Exception as e:
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
            # Atualiza primeira planilha (todos os dados)
            values1 = [[client_data[field] for field in [
                'nome_completo', 'nacionalidade', 'estado_civil', 'profissao',
                'email', 'celular', 'data_nascimento', 'rg', 'cpf',
                'caso', 'assunto_caso', 'responsavel_comercial',
                'endereco', 'bairro', 'cidade', 'estado', 'cep'
            ]]]
            self.update_sheet(SHEET_ID_1, 'A:Q', values1)
            
            # Atualiza segunda planilha (dados específicos)
            current_date = datetime.now().strftime('%d/%m/%Y')
            values2 = [[
                client_data['nome_completo'],
                current_date,
                client_data['responsavel_comercial'],
                client_data['caso'],
                client_data['assunto_caso'],
                "Em andamento",
                client_data['nome_completo'],
                folder_url
            ]]
            self.update_sheet(SHEET_ID_2, 'A:H', values2)
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar planilhas: {str(e)}") 