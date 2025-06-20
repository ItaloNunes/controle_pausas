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
except:
    funcionarios_df = pd.DataFrame(columns=["nome", "matricula", "cargo", "setor"])
    escrever_aba(planilha, "funcionarios", funcionarios_df)

# ========== CRUD FUNCIONÁRIOS (APENAS ADMIN) ==========
if st.session_state.perfil == "admin":
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
            atualizar = st.form_submit_button("📅 Atualizar")
            deletar = st.form_submit_button("🗑️ Excluir")

            if atualizar:
                idx = funcionarios_df[funcionarios_df["nome"] == editar_nome].index[0]
                funcionarios_df.loc[idx] = [nome_novo, matricula_novo, cargo_novo, setor_novo]
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success("Funcionário atualizado com sucesso.")

            if deletar:
                funcionarios_df = funcionarios_df[funcionarios_df["nome"] != editar_nome]
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success("Funcionário excluído com sucesso.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ➕ Cadastrar novo funcionário")

    with st.sidebar.form("novo_funcionario"):
        novo_nome = st.text_input("Nome", key="nome_novo")
        novo_matricula = st.text_input("Matrícula", key="matricula_novo")
        novo_cargo = st.text_input("Cargo", key="cargo_novo")
        novo_setor = st.text_input("Setor", key="setor_novo")
        cadastrar = st.form_submit_button("✅ Cadastrar")

        if cadastrar:
            if novo_nome and novo_nome not in funcionarios_df["nome"].values:
                novo_func = pd.DataFrame([{ "nome": novo_nome, "matricula": novo_matricula, "cargo": novo_cargo, "setor": novo_setor }])
                funcionarios_df = pd.concat([funcionarios_df, novo_func], ignore_index=True)
                escrever_aba(planilha, "funcionarios", funcionarios_df)
                st.sidebar.success(f"Funcionário '{novo_nome}' cadastrado com sucesso!")
            elif novo_nome in funcionarios_df["nome"].values:
                st.sidebar.warning("Funcionário já está cadastrado.")
            else:
                st.sidebar.warning("O campo nome é obrigatório.")

# ========== REGISTRO DE PAUSAS ==========
st.title("🕒 Controle de Pausas")

if funcionarios_df.empty:
    st.warning("⚠️ Nenhum funcionário cadastrado.")
    st.stop()

if "pausas_ativas" not in st.session_state:
    st.session_state["pausas_ativas"] = {}

nome = st.selectbox("Selecione o funcionário:", funcionarios_df["nome"].tolist())

col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Iniciar pausa"):
        if nome not in st.session_state["pausas_ativas"]:
            st.session_state["pausas_ativas"][nome] = datetime.now()
            st.success(f"Pausa iniciada para {nome}")
        else:
            st.warning(f"{nome} já está em pausa.")

with col2:
    if st.button("⏹ Finalizar pausa"):
        inicio = st.session_state["pausas_ativas"].get(nome)
        if inicio:
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
            del st.session_state["pausas_ativas"][nome]
            st.success(f"Pausa finalizada para {nome}: {duracao}")
        else:
            st.warning(f"{nome} não está em pausa.")

# ========== RELATÓRIOS ==========
st.subheader("🔎 Filtrar pausas")
try:
    pausas_df = ler_aba(planilha, "pausas")
except:
    pausas_df = pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])

if not pausas_df.empty:
    pausas_df["inicio"] = pd.to_datetime(pausas_df["inicio"])
    pausas_df["fim"] = pd.to_datetime(pausas_df["fim"])

    data_filtro = st.date_input("Data:", datetime.now().date())
    nomes_filtro = ["Todos"] + funcionarios_df["nome"].tolist()
    usuario_filtro = st.selectbox("Funcionário para filtrar:", nomes_filtro)

    df_filtro = pausas_df.copy()
    df_filtro["data"] = df_filtro["inicio"].dt.date
    df_filtro = df_filtro[df_filtro["data"] == data_filtro]
    if usuario_filtro != "Todos":
        df_filtro = df_filtro[df_filtro["funcionario"] == usuario_filtro]

    st.dataframe(df_filtro)

    try:
        excel_buffer = io.BytesIO()
        df_filtro.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)
        st.download_button(
            label="📅 Baixar Excel",
            data=excel_buffer,
            file_name="pausas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")

    def mmss_para_segundos(valor):
        try:
            m, s = map(int, str(valor).split(":"))
            return m * 60 + s
        except:
            return 0

    pausas_df["duracao_segundos"] = pausas_df["duracao"].apply(mmss_para_segundos)

    resumo = pausas_df.groupby("funcionario")["duracao_segundos"].agg(
        total_pausas="count",
        total_minutos=lambda x: round(x.sum() / 60, 2),
        media_minutos=lambda x: round(x.mean() / 60, 2)
    ).reset_index()

    st.subheader("📊 Resumo por funcionário")
    st.dataframe(resumo)
