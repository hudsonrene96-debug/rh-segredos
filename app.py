import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="BI de Recursos Humanos - Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    tentativas = [{'encoding': 'latin1'}, {'encoding': 'iso-8859-1'}, {'encoding': 'utf-8-sig'}, {'encoding': 'cp1252'}]
    
    for config in tentativas:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=config['encoding'], on_bad_lines='skip')
            if df.empty or len(df.columns) < 2: continue
            
            # Limpar nomes das colunas (remover espaços e colocar em maiúsculas)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Conversão Financeira
            col_valor = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_valor:
                df['VALOR_NUM'] = pd.to_numeric(df[col_valor].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Conversão de Data
            col_data = next((c for c in df.columns if 'DT' in c or 'DATA' in c), None)
            if col_data:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df[col_data], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except: continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    st.markdown("---")

    # --- IDENTIFICAÇÃO AUTOMÁTICA DE COLUNAS ---
    # Tentamos encontrar as colunas por palavras-chave
    col_emp = next((c for c in df.columns if 'EMP' in c or 'COD' in c), df.columns[0])
    col_hist = next((c for c in df.columns if 'HIST' in c or 'NAT' in c), df.columns[1])
    col_func = next((c for c in df.columns if 'RAZAO' in c or 'NOME' in c or 'FUNC' in c), df.columns[2])

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros Avançados")
    
    lista_empresas = sorted(df[col_emp].unique().astype(str))
    sel_empresas = st.sidebar.multiselect(f"Empresa ({col_emp}):", options=lista_empresas)

    lista_hist = sorted(df[col_hist].unique().astype(str))
    sel_hist = st.sidebar.multiselect(f"Natureza/Histórico ({col_hist}):", options=lista_hist)

    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect(f"Funcionário ({col_func}):", options=lista_func)

    # Aplicação dos Filtros
    df_f = df.copy()
    if sel_empresas: df_f = df_f[df_f[col_emp].astype(str).isin(sel_empresas)]
    if sel_hist:     df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func:     df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES ---
    v_col = 'VALOR_NUM' if 'VALOR_NUM' in df_f.columns else df_f.columns[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Total Gasto", f"R$ {df_f[v_col].sum():,.2f}")
    c2.metric("👥 Colaboradores", len(df_f[col_func].unique()))
    
    maior_val = df_f[v_col].max() if not df_f.empty else 0
    menor_val = df_f[df_f[v_col] > 0][v_col].min() if not df_f.empty else 0
    
    c3.metric("📈 Maior Valor", f"R$ {maior_val:,.2f}")
    c4.metric("📉 Menor Valor", f"R$ {menor_val:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("🏆 Top 10 Gastos por Funcionário")
        rank = df_f.groupby(col_func)[v_col].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(rank, x=v_col, y=col_func, orientation='h', color=v_col, color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)

    with g2:
        st.subheader("🍕 Distribuição por Natureza")
        fig_pie = px.pie(df_f, values=v_col, names=col_hist, hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA ---
    st.subheader("📑 Tabela de Dados")
    st.dataframe(df_f, use_container_width=True)

else:
    st.error("Não foi possível carregar os dados. Verifique se o arquivo FUNCIONARIOS.csv está correto.")
