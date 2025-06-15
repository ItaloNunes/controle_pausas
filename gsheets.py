import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Conecta à planilha do Google
def conectar_planilha(nome_planilha):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    try:
        return client.open(nome_planilha)
    except Exception as e:
        st.error(f"❌ Erro ao abrir a planilha '{nome_planilha}'. Verifique se ela existe e se está compartilhada com o e-mail do serviço.")
        st.stop()

# Lê aba da planilha e retorna como DataFrame
def ler_aba(planilha, nome_aba):
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
    dados = aba.get_all_records()
    return pd.DataFrame(dados)

# Escreve DataFrame na aba (sobrescreve)
def escrever_aba(planilha, nome_aba, df):
    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.exceptions.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
    except Exception as e:
        st.error(f"Erro ao acessar ou criar a aba '{nome_aba}': {e}")
        st.stop()

    aba.clear()
    if not df.empty:
        aba.update([df.columns.values.tolist()] + df.values.tolist())
    else:
        aba.update([["vazio"]])
