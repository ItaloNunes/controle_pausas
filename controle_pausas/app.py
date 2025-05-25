import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os

# ===================== ARQUIVOS =====================
df_path = "pausas.csv"
funcionarios_path = "funcionarios.csv"

# ===================== CARREGAR FUNCIONÁRIOS =====================
if not os.path.exists(funcionarios_path):
    funcionarios_df = pd.DataFrame(columns=["nome", "matricula", "cargo", "setor"])
    funcionarios_df.to_csv(funcionarios_path, index=False)
else:
    funcionarios_df = pd.read_csv(funcionarios_path)

# ===================== CRUD DE FUNCIONÁRIOS =====================
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
            st.sidebar.success(f"Funcionário '{editar_nome}' atualizado com sucesso!")

        if deletar:
            funcionarios_df = funcionarios_df[funcionarios_df["nome"] != editar_nome]
            funcionarios_df.to_csv(funcionarios_path, index=False)
            st.sidebar.success(f"Funcionário '{editar_nome}' excluído com sucesso!")

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
            novo_func = pd.DataFrame([{
                "nome": novo_nome,
                "matricula": novo_matricula,
                "cargo": novo_cargo,
                "setor": novo_setor
            }])
            funcionarios_df = pd.concat([funcionarios_df, novo_func], ignore_index=True)
            funcionarios_df.to_csv(funcionarios_path, index=False)
            st.sidebar.success(f"Funcionário '{novo_nome}' cadastrado com sucesso!")
        elif novo_nome in funcionarios_df["nome"].values:
            st.sidebar.warning("Funcionário já está cadastrado.")
        else:
            st.sidebar.warning("O campo nome é obrigatório.")

# ===================== CONTROLE DE PAUSAS =====================
st.title("🕒 Controle de Pausas")

if "df" not in st.session_state:
    try:
        df = pd.read_csv(df_path, parse_dates=["inicio", "fim"])
    except FileNotFoundError:
        df = pd.DataFrame(columns=["funcionario", "inicio", "fim", "duracao"])
    st.session_state.df = df

if len(funcionarios_df) == 0:
    st.warning("⚠️ Nenhum funcionário cadastrado. Cadastre primeiro no menu lateral.")
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
                st.session_state["pausa_inicio"] = None
                st.success(f"Pausa finalizada: {duracao} minutos")
                st.session_state.df.to_csv(df_path, index=False)
            else:
                st.warning("Você precisa iniciar a pausa primeiro.")

    # ===================== FILTROS E RELATÓRIOS =====================
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

    # Exportar CSV (funciona em qualquer ambiente)
    csv_buffer = io.StringIO()
    df_filtro.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Baixar CSV",
        data=csv_buffer.getvalue(),
        file_name="pausas.csv",
        mime="text/csv"
    )

    # Resumo por funcionário
    st.subheader("📊 Resumo por funcionário")
    resumo = st.session_state.df.groupby("funcionario")["duracao"].agg(
        total_pausas="count",
        total_minutos="sum",
        media_minutos="mean"
    ).round(2).reset_index()
    st.dataframe(resumo)
# ===================== RODAPÉ =====================
# ===================== ASSINATURA CENTRAL =====================
# ===================== RODAPÉ CENTRAL =====================
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
            z-index: 100;
        }
    </style>
    <div class="footer-text">Developer by <strong>INV</strong></div>
    """,
    unsafe_allow_html=True
)

