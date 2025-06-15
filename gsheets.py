import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Conecta à planilha do Google
def conectar_planilha(nome_planilha):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

# Lê aba da planilha e retorna como DataFrame
def ler_aba(planilha, nome_aba):
    aba = planilha.worksheet(nome_aba)
    dados = aba.get_all_records()
    return pd.DataFrame(dados)

# Escreve DataFrame na aba (sobrescreve)
def escrever_aba(planilha, nome_aba, df):
    aba = planilha.worksheet(nome_aba)
    aba.clear()
    aba.update([df.columns.values.tolist()] + df.values.tolist())
