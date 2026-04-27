import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="Gestão de RH Estratégica", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    tentativas = [{'encoding': 'latin1'}, {'encoding': 'iso-8859-1'}, {'encoding': 'utf-8-sig'}, {'encoding': 'cp1252'}]
    
    for config in tentativas:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=config['encoding'], on_bad_lines='skip')
            if df.empty or len(df.columns) < 2: continue
            
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Limpeza Financeira
            if 'VLRDESDOB' in df.columns:
                df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Conversão de Data
            if 'DTNEG' in df.columns:
                df['DATA'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except: continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    st.markdown("---")

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros Avançados")
    
    # Filtro de Empresa
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    lista_empresas = sorted(df[col_emp].unique().astype(str))
    sel_empresas = st.sidebar.multiselect("Filtrar por Empresa:", options=lista_empresas)

    # Filtro de Natureza (Histórico)
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else df.columns[1]
    lista_hist = sorted(df[col_hist].unique().astype(str))
    sel_hist = st.sidebar.multiselect("Filtrar por Natureza:", options=lista_hist)

    # Filtro de Funcionário
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[2]
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Filtrar por Funcionário:", options=lista_func)

    # Aplicação dos Filtros
    df_f = df.copy()
    if sel_empresas: df_f = df_f[df_f[col_emp].astype(str).isin(sel_empresas)]
    if sel_hist:     df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func:     df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES (CARDS) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Gasto", f"R$ {df_f['VLRDESDOB'].sum():,.2f}")
    c2.metric("👥 Colaboradores", len(df_f[col_func].unique()))
    
    # Maior e Menor Salário/Valor encontrado no filtro atual
    maior_val = df_f['VLRDESDOB'].max() if not df_f.empty else 0
    menor_val = df_f[df_f['VLRDESDOB'] > 0]['VLRDESDOB'].min() if not df_f.empty else 0
    
    c3.metric("📈 Maior Valor", f"R$ {maior_val:,.2f}")
    c4.metric("📉 Menor Valor", f"R$ {menor_val:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("🏆 Top 10 Maiores Custos")
        rank = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(rank, x='VLRDESDOB', y=col_func, orientation='h', 
                         color='VLRDESDOB', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🍕 Distribuição por Natureza")
        # Gráfico de Pizza (Donut)
        fig_pie = px.pie(df_f, values='VLRDESDOB', names=col_hist, hole=0.5,
                         color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA ---
    st.subheader("📑 Detalhamento dos Lançamentos")
    df_tab = df_f.copy()
    if 'DATA' in df_tab.columns:
        df_tab['DATA'] = df_tab['DATA'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_tab, use_container_width=True)

else:
    st.error("Erro ao carregar os filtros. Verifique o arquivo CSV.")
