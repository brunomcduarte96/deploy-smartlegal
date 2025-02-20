import streamlit as st

# Configurações do Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# Configurações do Google
GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
SHEETS_SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
DRIVE_SCOPE = ['https://www.googleapis.com/auth/drive']
DOCS_SCOPE = ['https://www.googleapis.com/auth/documents']

# IDs das planilhas do Google Sheets
SHEET_ID_1 = st.secrets["SHEET_ID_1"]
SHEET_ID_2 = st.secrets["SHEET_ID_2"]

# ID da pasta raiz no Google Drive
ROOT_FOLDER_ID = st.secrets["ROOT_FOLDER_ID"]

# Configurações do OpenAI
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# URLs do Menu
URLS = {
    "CLIENTES_SMARTLEGAL": st.secrets["URL_CLIENTES"],
    "PROCESSOS_ANDAMENTO": st.secrets["URL_PROCESSOS"],
    "LEADS_ADS": st.secrets["URL_LEADS"],
    "CRM_RD": st.secrets["URL_CRM"],
    "DRIVE_GMAIL": st.secrets["URL_DRIVE"]
} 