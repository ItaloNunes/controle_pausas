import streamlit as st
import pandas as pd
from datetime import datetime
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# =============== CONFIGURAÇÃO ===================
st.set_page_config(page_title="Controle de Pausas", layout="wide")

# Autenticando com Google Sheets via secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(credentials)

SHEET_NAME = "controle_pausas"
ABA_FUNCIONARIOS = "funcionarios"
ABA_PAUSAS = "pausas"

# =============== PLANILHA ===================
try:
    sheet = client.open(SHEET_NAME)
except gspread.SpreadsheetNotFound:
    sheet = client.create(SHEET_NAME)
    sheet.share(credentials_dict["client_email"], perm_type="user", role="writer")
    sheet.add_worksheet(title=ABA_FUNCIONARIOS, rows="1000", cols="20")
    sheet.add_worksheet(title=ABA_PAUSAS, rows="1000", cols="20")
    sheet.del_worksheet(sheet.worksheet("Sheet1"))

    # Cabeçalhos iniciais
    sheet.worksheet(ABA_FUNCIONARIOS).update([["nome", "matricula", "cargo", "setor"]])
    sheet.worksheet(ABA_PAUSAS).update([["funcionario", "inicio", "fim", "duracao"]])

# =============== FUNÇÕES ===================
def carregar_funcionarios():
    try:
        dados = sheet.worksheet(ABA_FUNCIONARIOS).get_all_records()
        return pd.DataFrame(dados)
    except Exception:
        return pd.DataFrame(columns=["nome", "matricula", "cargo", "setor"])

def salvar_funcionarios(df):
    aba = sheet.worksheet(ABA_FUNCIONARIOS)
    aba.clear()
    aba.update([df.columns.values.tolist()] + df.values.tolist())

def carregar_pausas():
    try:
        dados = sheet.worksheet(ABA_PAUSAS).get_all_records()
        df = pd.DataFrame(dados)
        df["inicio"] = pd.to_datetime(df["inicio"])
        df["fim"] = pd.to_datetime(df["fim"])
        return df
    except Exception:
        return pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])

def salvar_pausas(df):
    aba = sheet.worksheet(ABA_PAUSAS)
    aba.clear()
    df["inicio"] = df["inicio"].astype(str)
    df["fim"] = df["fim"].astype(str)
    aba.update([df.columns.values.tolist()] + df.values.tolist())

# =============== LOGIN ===================
usuarios = {
    "admin": {"senha": "1234", "tipo": "admin"},
    "operador1": {"senha": "op123", "tipo": "operador"},
    "operador2": {"senha": "op456", "tipo": "operador"}
}

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.title("🔐 Login do Sistema")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user in usuarios and usuarios[user]["senha"] == password:
            st.session_state.usuario_logado = user
            st.success(f"Bem-vindo, {user}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválido.")
    st.stop()

tipo_usuario = usuarios[st.session_state.usuario_logado]["tipo"]

# =============== LOGO ===================
st.markdown(
    """
    <div style='text-align: center; margin-top: -25px; margin-bottom: 10px;'>
        <img src='https://raw.githubusercontent.com/ItaloNunes/controle_pausas/main/controle_pausas/logo%20ABJ.jpg' width='160'/>
    </div>
    """,
    unsafe_allow_html=True
)

st.title("🕒 Controle de Pausas")

# =============== CARREGAMENTO INICIAL ===================
funcionarios_df = carregar_funcionarios()
if "df" not in st.session_state:
    st.session_state.df = carregar_pausas()

# =============== CRUD FUNCIONÁRIOS (ADMIN) ===================
if tipo_usuario == "admin":
    st.sidebar.title("📋 Cadastro de Funcionários")
    st.sidebar.markdown("### 👀 Funcionários cadastrados")
    st.sidebar.dataframe(funcionarios_df)

    nomes = funcionarios_df["nome"].tolist()
    editar_nome = st.sidebar.selectbox("Editar/Excluir funcionário:", [""] + nomes)

    if editar_nome:
        funcionario = funcionarios_df[funcionarios_df["nome"] == editar_nome].iloc[0]
        with st.sidebar.form("editar_form"):
            nome_novo = st.text_input("Nome", funcionario["nome"])
            matricula_novo = st.text_input("Matrícula", funcionario["matricula"])
            cargo_novo = st.text_input("Cargo", funcionario["cargo"])
            setor_novo = st.text_input("Setor", funcionario["setor"])
            atualizar = st.form_submit_button("💾 Atualizar")
            deletar = st.form_submit_button("🗑️ Excluir")

            if atualizar:
                index = funcionarios_df[funcionarios_df["nome"] == editar_nome].index[0]
                funcionarios_df.loc[index] = [nome_novo, matricula_novo, cargo_novo, setor_novo]
                salvar_funcionarios(funcionarios_df)
                st.sidebar.success(f"Funcionário '{editar_nome}' atualizado!")

            if deletar:
                funcionarios_df = funcionarios_df[funcionarios_df["nome"] != editar_nome]
                salvar_funcionarios(funcionarios_df)
                st.sidebar.success(f"Funcionário '{editar_nome}' excluído!")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ➕ Cadastrar novo funcionário")
    with st.sidebar.form("novo_funcionario"):
        novo_nome = st.text_input("Nome")
        novo_matricula = st.text_input("Matrícula")
        novo_cargo = st.text_input("Cargo")
        novo_setor = st.text_input("Setor")
        cadastrar = st.form_submit_button("✅ Cadastrar")

        if cadastrar:
            if novo_nome and novo_nome not in funcionarios_df["nome"].values:
                novo_func = pd.DataFrame([{
                    "nome": novo_nome,
                    "matricula": novo_matricula,
                    "cargo": novo_cargo,
                    "setor": novo_setor
                }])
                funcionarios_df = pd.concat([funcionarios_df, novo_func], ignore_index=True)
                salvar_funcionarios(funcionarios_df)
                st.sidebar.success(f"Funcionário '{novo_nome}' cadastrado!")
            elif novo_nome in funcionarios_df["nome"].values:
                st.sidebar.warning("Funcionário já cadastrado.")
            else:
                st.sidebar.warning("O campo nome é obrigatório.")

# =============== REGISTRO DE PAUSAS ===================
if len(funcionarios_df) == 0:
    st.warning("⚠️ Nenhum funcionário cadastrado.")
else:
    nome = st.selectbox("Selecione o funcionário:", funcionarios_df["nome"].tolist())

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Iniciar pausa"):
            st.session_state["pausa_inicio"] = datetime.now()
            st.session_state["pausa_nome"] = nome
            st.success(f"Pausa iniciada para {nome}")

    with col2:
        if st.button("⏹ Finalizar pausa"):
            inicio = st.session_state.get("pausa_inicio")
            nome = st.session_state.get("pausa_nome")
            if inicio and nome:
                fim = datetime.now()
                duracao = round((fim - inicio).total_seconds() / 60, 2)
                nova = pd.DataFrame([{
                    "funcionario": nome,
                    "inicio": inicio,
                    "fim": fim,
                    "duracao": duracao
                }])
                st.session_state.df = pd.concat([st.session_state.df, nova], ignore_index=True)
                salvar_pausas(st.session_state.df)
                st.session_state["pausa_inicio"] = None
                st.success(f"Pausa finalizada: {duracao} minutos")
            else:
                st.warning("Você precisa iniciar a pausa primeiro.")

# =============== RELATÓRIO E FILTRO ===================
st.subheader("🔎 Filtrar pausas")
data_filtro = st.date_input("Data:", datetime.now().date())
nomes_filtro = ["Todos"] + funcionarios_df["nome"].tolist()
usuario_filtro = st.selectbox("Funcionário para filtrar:", nomes_filtro)

df_filtro = st.session_state.df.copy()
df_filtro["data"] = pd.to_datetime(df_filtro["inicio"]).dt.date
df_filtro = df_filtro[df_filtro["data"] == data_filtro]
if usuario_filtro != "Todos":
    df_filtro = df_filtro[df_filtro["funcionario"] == usuario_filtro]

st.dataframe(df_filtro)

csv_buffer = io.StringIO()
df_filtro.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")
st.download_button("📥 Baixar CSV", csv_buffer.getvalue(), file_name="pausas.csv", mime="text/csv")

# =============== RESUMO ===================
st.subheader("📊 Resumo por funcionário")
resumo = st.session_state.df.groupby("funcionario")["duracao"].agg(
    total_pausas="count", total_minutos="sum", media_minutos="mean"
).round(2).reset_index()
st.dataframe(resumo)

# =============== RODAPÉ ===================
st.markdown("""
    <style>
        .footer-text {
            position: fixed;
            bottom: 15px;
            width: 100%;
            text-align: center;
            font-size: 14px;
            color: gray;
            opacity: 0.6;
            z-index: 100;
        }
    </style>
    <div class="footer-text">Developer by <strong>INV</strong></div>
""", unsafe_allow_html=True)
