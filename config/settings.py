import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configurações do Google
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SHEETS_SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
DRIVE_SCOPE = ['https://www.googleapis.com/auth/drive']
DOCS_SCOPE = ['https://www.googleapis.com/auth/documents']

# IDs das planilhas do Google Sheets
SHEET_ID_1 = os.getenv("SHEET_ID_1")
SHEET_ID_2 = os.getenv("SHEET_ID_2")

# ID da pasta raiz no Google Drive
ROOT_FOLDER_ID = os.getenv("ROOT_FOLDER_ID")

# Configurações do OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# URLs do Menu
URLS = {
    "CLIENTES_SMARTLEGAL": os.getenv("URL_CLIENTES"),
    "PROCESSOS_ANDAMENTO": os.getenv("URL_PROCESSOS"),
    "LEADS_ADS": os.getenv("URL_LEADS"),
    "CRM_RD": os.getenv("URL_CRM"),
    "DRIVE_GMAIL": os.getenv("URL_DRIVE")
} 