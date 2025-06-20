import streamlit as st
import pandas as pd
from datetime import datetime
import io
from gsheets import conectar_planilha, ler_aba, escrever_aba

# ========== LOGIN E PERFIS ==========
USUARIOS = {
    "admin": {"senha": "admin123", "perfil": "admin"},
    "operador": {"senha": "1234", "perfil": "operador"}
}

if "usuario" not in st.session_state:
    st.session_state.usuario = None
    st.session_state.perfil = None

if not st.session_state.usuario:
    st.title("🔐 Login do Sistema")
    usuario = st.selectbox("Usuário", list(USUARIOS.keys()))
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if USUARIOS.get(usuario) and USUARIOS[usuario]["senha"] == senha:
            st.session_state.usuario = usuario
            st.session_state.perfil = USUARIOS[usuario]["perfil"]
            st.success(f"✅ Logado como {usuario}")
            st.rerun()
        else:
            st.error("❌ Usuário ou senha incorretos.")
    st.stop()

# ========== CONECTAR À PLANILHA ==========
planilha = conectar_planilha("controle_pausas")

# ========== FUNCIONÁRIOS ==========
try:
    funcionarios_df = ler_aba(planilha, "funcionarios")
    if set(funcionarios_df.columns) != {"nome", "matricula", "cargo", "setor"}:
        raise ValueError("Colunas incorretas")
except:
    funcionarios_df = pd.DataFrame(columns=["nome", "matricula", "cargo", "setor"])
    escrever_aba(planilha, "funcionarios", funcionarios_df)

# ========== CRUD FUNCIONÁRIOS (APENAS ADMIN) ==========
if st.session_state.perfil == "admin":
    st.sidebar.title("📋 Cadastro de Funcionários")
    st.sidebar.dataframe(funcionarios_df)

    nomes = funcionarios_df["nome"].tolist()
    editar_nome = st.sidebar.selectbox("Editar/Excluir funcionário:", [""] + nomes)

    if editar_nome:
        func = funcionarios_df[funcionarios_df["nome"] == editar_nome].iloc[0]
        with st.sidebar.form("editar_form"):
            nome_novo = st.text_input("Nome", func["nome"], key="edit_nome")
            matricula = st.text_input("Matrícula", func["matricula"], key="edit_mat")
            cargo = st.text_input("Cargo", func["cargo"], key="edit_cargo")
            setor = st.text_input("Setor", func["setor"], key="edit_setor")
            atualizar = st.form_submit_button("📏 Atualizar")
            deletar = st.form_submit_button("🗑️ Excluir")

            if atualizar:
                idx = funcionarios_df[funcionarios_df["nome"] == editar_nome].index[0]
                funcionarios_df.loc[idx] = [nome_novo, matricula, cargo, setor]
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success("Atualizado.")
            if deletar:
                funcionarios_df = funcionarios_df[funcionarios_df["nome"] != editar_nome]
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success("Excluído.")

    st.sidebar.markdown("---")
    with st.sidebar.form("novo_form"):
        nome = st.text_input("Nome")
        matricula = st.text_input("Matrícula")
        cargo = st.text_input("Cargo")
        setor = st.text_input("Setor")
        cadastrar = st.form_submit_button("✅ Cadastrar")
        if cadastrar:
            if nome and nome not in funcionarios_df["nome"].values:
                novo = pd.DataFrame([{"nome": nome, "matricula": matricula, "cargo": cargo, "setor": setor}])
                funcionarios_df = pd.concat([funcionarios_df, novo], ignore_index=True)
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success("Funcionário cadastrado.")
            elif nome in funcionarios_df["nome"].values:
                st.sidebar.warning("Nome já existe.")
            else:
                st.sidebar.warning("Nome obrigatório.")

# ========== REGISTRO DE PAUSAS ==========
st.title("🕒 Controle de Pausas")

if funcionarios_df.empty:
    st.warning("Nenhum funcionário cadastrado.")
    st.stop()

# Inicializa pausas simultâneas
if "pausas_ativas" not in st.session_state:
    st.session_state["pausas_ativas"] = {}

nome = st.selectbox("Funcionário:", funcionarios_df["nome"].tolist())

col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Iniciar pausa"):
        st.session_state["pausas_ativas"][nome] = datetime.now()
        st.success(f"Pausa iniciada para {nome}")

with col2:
    if st.button("⏹ Finalizar pausa"):
        if nome in st.session_state["pausas_ativas"]:
            inicio = st.session_state["pausas_ativas"].pop(nome)
            fim = datetime.now()
            total_segundos = int((fim - inicio).total_seconds())
            minutos = total_segundos // 60
            segundos = total_segundos % 60
            duracao = f"{minutos:02d}:{segundos:02d}"

            try:
                pausas_df = ler_aba(planilha, "pausas")
            except:
                pausas_df = pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])

            nova = pd.DataFrame([{
                "funcionario": nome,
                "inicio": inicio.strftime("%Y-%m-%d %H:%M:%S"),
                "fim": fim.strftime("%Y-%m-%d %H:%M:%S"),
                "duracao": duracao
            }])
            pausas_df = pd.concat([pausas_df, nova], ignore_index=True)
            escrever_aba(planilha, "pausas", pausas_df)
            st.success(f"Pausa finalizada: {duracao}")
        else:
            st.warning("Nenhuma pausa ativa para esse funcionário.")

# ========== RELATÓRIO ==========
st.subheader("🔍 Filtrar Pausas")
try:
    pausas_df = ler_aba(planilha, "pausas")
except:
    pausas_df = pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])

if not pausas_df.empty:
    pausas_df["inicio"] = pd.to_datetime(pausas_df["inicio"])
    pausas_df["fim"] = pd.to_datetime(pausas_df["fim"])

    data_filtro = st.date_input("Data:", datetime.now().date())
    nomes_filtro = ["Todos"] + funcionarios_df["nome"].tolist()
    filtro_nome = st.selectbox("Funcionário:", nomes_filtro)

    df_filtro = pausas_df.copy()
    df_filtro["data"] = df_filtro["inicio"].dt.date
    df_filtro = df_filtro[df_filtro["data"] == data_filtro]
    if filtro_nome != "Todos":
        df_filtro = df_filtro[df_filtro["funcionario"] == filtro_nome]

    st.dataframe(df_filtro)

    buffer = io.BytesIO()
    df_filtro.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    st.download_button("📥 Baixar Excel", buffer, "pausas.xlsx")

    def mmss_para_segundos(txt):
        try:
            m, s = map(int, str(txt).split(":"))
            return m * 60 + s
        except:
            return 0

    pausas_df["duracao_seg"] = pausas_df["duracao"].apply(mmss_para_segundos)

    resumo = pausas_df.groupby("funcionario")["duracao_seg"].agg(
        total_pausas="count",
        total_minutos=lambda x: round(x.sum() / 60, 2),
        media_minutos=lambda x: round(x.mean() / 60, 2)
    ).reset_index()

    st.subheader("📊 Resumo por Funcionário")
    st.dataframe(resumo)
