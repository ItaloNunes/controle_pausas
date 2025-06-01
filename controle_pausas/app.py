import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# =============== CONFIGURAÇÕES ===================
st.set_page_config(page_title="Controle de Pausas", layout="wide")

df_path = "pausas.csv"
funcionarios_path = "funcionarios.csv"

usuarios = {
    "admin": {"senha": "1234", "tipo": "admin"},
    "operador1": {"senha": "op123", "tipo": "operador"},
    "operador2": {"senha": "op456", "tipo": "operador"}
}

# =============== LOGIN ===================
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if st.session_state.usuario_logado is None:
    st.title("🔐 Login do Sistema")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if st.button("Entrar"):
    if user in usuarios and usuarios[user]["senha"] == password:
        st.session_state.usuario_logado = user
        st.success(f"Bem-vindo, {user}!")
        st.rerun()  # ✅ correto para versão nova
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

tipo_usuario = usuarios[st.session_state.usuario_logado]["tipo"]

# =============== LOGO CENTRALIZADA ===================
st.markdown(
    """
    <div style='text-align: center; margin-top: -25px; margin-bottom: 10px;'>
        <img src='https://raw.githubusercontent.com/ItaloNunes/controle_pausas/main/controle_pausas/logo%20ABJ.jpg' width='160'/>
    </div>
    """,
    unsafe_allow_html=True
)
st.title("🕒 Controle de Pausas")

# =============== CARREGAR FUNCIONÁRIOS ===================
if not os.path.exists(funcionarios_path):
    funcionarios_df = pd.DataFrame(columns=["nome", "matricula", "cargo", "setor"])
    funcionarios_df.to_csv(funcionarios_path, index=False)
else:
    funcionarios_df = pd.read_csv(funcionarios_path)

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
            nome_novo = st.text_input("Nome", funcionario["nome"], key="nome_edit")
            matricula_novo = st.text_input("Matrícula", funcionario["matricula"], key="matricula_edit")
            cargo_novo = st.text_input("Cargo", funcionario["cargo"], key="cargo_edit")
            setor_novo = st.text_input("Setor", funcionario["setor"], key="setor_edit")
            atualizar = st.form_submit_button("💾 Atualizar")
            deletar = st.form_submit_button("🗑️ Excluir")

            if atualizar:
                index = funcionarios_df[funcionarios_df["nome"] == editar_nome].index[0]
                funcionarios_df.loc[index] = [nome_novo, matricula_novo, cargo_novo, setor_novo]
                funcionarios_df.to_csv(funcionarios_path, index=False)
                st.experimental_rerun()

            if deletar:
                funcionarios_df = funcionarios_df[funcionarios_df["nome"] != editar_nome]
                funcionarios_df.to_csv(funcionarios_path, index=False)
                st.experimental_rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ➕ Novo Funcionário")

    with st.sidebar.form("novo_funcionario"):
        novo_nome = st.text_input("Nome", key="nome_novo")
        novo_matricula = st.text_input("Matrícula", key="matricula_novo")
        novo_cargo = st.text_input("Cargo", key="cargo_novo")
        novo_setor = st.text_input("Setor", key="setor_novo")
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
                funcionarios_df.to_csv(funcionarios_path, index=False)
                st.experimental_rerun()
            elif novo_nome in funcionarios_df["nome"].values:
                st.sidebar.warning("Funcionário já cadastrado.")
            else:
                st.sidebar.warning("O nome é obrigatório.")

# =============== CONTROLE DE PAUSAS ===================
if "df" not in st.session_state:
    try:
        df = pd.read_csv(df_path, parse_dates=["inicio", "fim"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])
    st.session_state.df = df

if len(funcionarios_df) == 0:
    st.warning("⚠️ Nenhum funcionário cadastrado.")
else:
    nome = st.selectbox("Funcionário:", funcionarios_df["nome"].tolist())

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
                st.session_state.df.to_csv(df_path, index=False)
                st.session_state["pausa_inicio"] = None
                st.success(f"Pausa finalizada: {duracao} minutos")
            else:
                st.warning("Você precisa iniciar a pausa antes.")

# =============== FILTRAR E EXPORTAR ===================
st.subheader("🔎 Filtrar Pausas")

data_filtro = st.date_input("Data:", datetime.now().date())
nomes_filtro = ["Todos"] + funcionarios_df["nome"].tolist()
usuario_filtro = st.selectbox("Filtrar por funcionário:", nomes_filtro)

df_filtro = st.session_state.df.copy()
df_filtro["data"] = pd.to_datetime(df_filtro["inicio"]).dt.date
df_filtro = df_filtro[df_filtro["data"] == data_filtro]
if usuario_filtro != "Todos":
    df_filtro = df_filtro[df_filtro["funcionario"] == usuario_filtro]

st.dataframe(df_filtro)

csv_buffer = io.StringIO()
df_filtro.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")
st.download_button("📥 Baixar CSV", csv_buffer.getvalue(), "pausas.csv", "text/csv")

# =============== RESUMO ===================
st.subheader("📊 Resumo por Funcionário")
resumo = st.session_state.df.groupby("funcionario")["duracao"].agg(
    total_pausas="count",
    total_minutos="sum",
    media_minutos="mean"
).round(2).reset_index()
st.dataframe(resumo)

# =============== RODAPÉ ===================
st.markdown(
    """
    <style>
        .footer-text {
            position: fixed;
            bottom: 15px;
            width: 100%;
            text-align: center;
            font-size: 14px;
            color: gray;
            opacity: 0.6;
        }
    </style>
    <div class="footer-text">Developer by <strong>INV</strong></div>
    """,
    unsafe_allow_html=True
)
