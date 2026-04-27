import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração de Página
st.set_page_config(page_title="Gestão de Pessoal | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados_rh():
    try:
        # Carregando o arquivo de funcionários
        df = pd.read_csv('FUNCIONARIOS.xls', sep=',', encoding='utf-8')
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Tratamento de Valores
        if 'VLRDESDOB' in df.columns:
            df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'], errors='coerce').fillna(0)
        
        # Tratamento de Datas (Formato Excel para Python)
        if 'DTNEG' in df.columns:
            # O Excel conta dias a partir de 30/12/1899
            df['DATA'] = pd.to_datetime(df['DTNEG'], unit='D', origin='1899-12-30', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo de RH: {e}")
        return None

df = carregar_dados_rh()

if df is not None:
    st.title("👥 Gestão de Custos e Pessoal - Bem Leve")
    
    # --- SIDEBAR FILTROS ---
    st.sidebar.header("🔍 Filtros Administrativos")
    
    # Filtro de Unidade (CODEMP)
    col_emp = 'CODEMP'
    lista_unidades = sorted(df[col_emp].unique().astype(str))
    sel_unidades = st.sidebar.multiselect("Filtrar por Unidade (CODEMP):", options=lista_unidades)
    
    # Filtro de Funcionário (RAZAOSOCIAL)
    col_func = 'RAZAOSOCIAL'
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Filtrar por Funcionário:", options=lista_func)
    
    # Filtro de Histórico (Tipo de Gasto)
    col_hist = 'HISTORICO'
    lista_hist = sorted(df[col_hist].dropna().unique().astype(str))
    sel_hist = st.sidebar.multiselect("Tipo de Lançamento (Histórico):", options=lista_hist)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    if sel_unidades:
        df_f = df_f[df_f[col_emp].astype(str).isin(sel_unidades)]
    if sel_func:
        df_f = df_f[df_f[col_func].isin(sel_func)]
    if sel_hist:
        df_f = df_f[df_f[col_hist].isin(sel_hist)]

    # --- MÉTRICAS PRINCIPAIS ---
    m1, m2, m3 = st.columns(3)
    total_pagos = df_f['VLRDESDOB'].sum()
    m1.metric("💰 Total Desembolsado", f"R$ {total_pagos:,.2f}")
    m2.metric("👥 Total Colaboradores", len(df_f[col_func].unique()))
    m3.metric("📑 Qtd. Lançamentos", len(df_f))

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("🏆 Maiores Gastos por Colaborador")
        rank_pessoal = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_func = px.bar(rank_pessoal, x='VLRDESDOB', y=col_func, orientation='h',
                          color='VLRDESDOB', color_continuous_scale='Sunsetdark',
                          labels={'VLRDESDOB': 'Valor Total (R$)', col_func: 'Colaborador'})
        st.plotly_chart(fig_func, use_container_width=True)

    with g2:
        st.subheader("📊 Distribuição por Tipo (Histórico)")
        if not df_f[col_hist].dropna().empty:
            fat_hist = df_f.groupby(col_hist)['VLRDESDOB'].sum().sort_values(ascending=False).head(8).reset_index()
            fig_pie = px.pie(fat_hist, values='VLRDESDOB', names=col_hist, hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem dados de Histórico para exibir.")

    # --- TABELA DE CONFERÊNCIA ---
    st.subheader("📑 Detalhamento de Lançamentos")
    # Selecionando colunas úteis e formatando a data para exibição
    df_ver = df_f[[col_func, 'VLRDESDOB', col_hist, col_emp, 'DATA']].copy()
    df_ver['DATA'] = df_ver['DATA'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_ver.sort_values('VLRDESDOB', ascending=False), use_container_width=True)

else:
    st.error("Não foi possível carregar o arquivo de Funcionários. Verifique se o nome do arquivo no GitHub está correto.")
