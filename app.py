import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="BI de Recursos Humanos - Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    # Testamos várias codificações para evitar o erro de 'utf-8'
    for enc in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            # LIMPEZA CRÍTICA: Remove espaços e caracteres estranhos dos nomes das colunas
            df.columns = [str(c).strip().upper().replace('Ó', 'O').replace('Í', 'I') for c in df.columns]
            
            # Tratamento do Valor Financeiro
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Tratamento da Data
            col_dt = next((c for c in df.columns if 'DT' in c or 'DATA' in c), None)
            if col_dt:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df[col_dt], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Identificação das colunas para os filtros
    col_emp = next((c for c in df.columns if 'EMP' in c or 'COD' in c), df.columns[0])
    col_hist = next((c for c in df.columns if 'HIST' in c or 'NAT' in c), None)
    col_func = next((c for c in df.columns if 'RAZAO' in c or 'NOME' in c), df.columns[1])

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    sel_emp = st.sidebar.multiselect("Filtrar por Empresa:", options=sorted(df[col_emp].unique().astype(str)))
    
    options_hist = sorted(df[col_hist].unique().astype(str)) if col_hist else []
    sel_hist = st.sidebar.multiselect("Filtrar por Natureza (Histórico):", options=options_hist)
    
    sel_func = st.sidebar.multiselect("Filtrar por Funcionário:", options=sorted(df[col_func].unique().astype(str)))

    # Aplicar Filtros
    df_f = df.copy()
    if sel_emp:  df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist: df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]
    if sel_func: df_f = df_f[df_f[col_func].astype(str).isin(sel_func)]

    # --- INDICADORES ---
    c1, c2, c3, c4 = st.columns(4)
    total = df_f['VALOR_PAGO'].sum()
    c1.metric("💰 Total Gasto", f"R$ {total:,.2f}")
    c2.metric("👥 Qtd. Funcionários", len(df_f[col_func].unique()))
    
    # Maior e Menor Salário (do filtro atual)
    maior = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    menor = df_f[df_f['VALOR_PAGO'] > 0]['VALOR_PAGO'].min() if not df_f.empty else 0
    c3.metric("📈 Maior Salário", f"R$ {maior:,.2f}")
    c4.metric("📉 Menor Salário", f"R$ {menor:,.2f}")

    st.markdown("---")

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏆 Top 10 Custos")
        rank = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig_bar = px.bar(rank, x='VALOR_PAGO', y=col_func, orientation='h', color='VALOR_PAGO', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with g2:
        st.subheader("🍕 Distribuição por Natureza")
        if col_hist:
            fig_pie = px.pie(df_f, values='VALOR_PAGO', names=col_hist, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA ---
    st.subheader("📑 Detalhamento")
    st.dataframe(df_f, use_container_width=True)
else:
    st.error("Erro ao processar o arquivo. Verifique se o nome no GitHub é 'FUNCIONARIOS.csv'")
