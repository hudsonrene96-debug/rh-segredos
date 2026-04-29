import pandas as pd
import plotly.express as px
import streamlit as st
import os

# Configuração inicial
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    if not os.path.exists(file_path):
        return None

    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # 1. Tratamento Financeiro
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # 2. NOVO Tratamento de Data (DTNEG) - Mais inteligente
            if 'DTNEG' in df.columns:
                # Tenta converter direto (caso seja texto tipo 03/30/2026)
                df['DATA_REF'] = pd.to_datetime(df['DTNEG'], errors='coerce')
                
                # Se falhou e ficou tudo nulo, tenta converter como número do Excel
                if df['DATA_REF'].isnull().all():
                    df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), 
                                                   unit='D', origin='1899-12-30', errors='coerce')
                
                # Remove horas se existirem para facilitar o filtro
                df['DATA_REF'] = df['DATA_REF'].dt.normalize()
            
            return df
        except:
            continue
    return None

df = carregar_dados()

if df is not None:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Mapeamento
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro de Data (Corrigido)
    periodo = None
    if 'DATA_REF' in df.columns and not df['DATA_REF'].isnull().all():
        # Limpa valores nulos apenas para o cálculo do slider
        df_datas = df.dropna(subset=['DATA_REF'])
        min_d, max_d = df_datas['DATA_REF'].min().date(), df_datas['DATA_REF'].max().date()
        
        # Se a data mínima for igual à máxima, o Streamlit pode reclamar, então validamos
        if min_d == max_d:
            st.sidebar.info(f"Data única detectada: {min_d.strftime('%d/%m/%Y')}")
            periodo = (min_d, max_d)
        else:
            periodo = st.sidebar.date_input("Filtrar Período:", value=(min_d, max_d))

    sel_emp = st.sidebar.multiselect("Empresa (CODEMP):", options=sorted(df[col_emp].unique().astype(str)))
    
    opcoes_hist = sorted(df[col_hist].dropna().unique().astype(str)) if col_hist else []
    sel_hist = st.sidebar.multiselect("Histórico/Natureza:", options=opcoes_hist)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    
    if periodo and isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df_f = df_f[(df_f['DATA_REF'].dt.date >= periodo[0]) & (df_f['DATA_REF'].dt.date <= periodo[1])]
    
    if sel_emp:
        df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist:
        df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]

    # --- DASHBOARD ---
    c1, c2, c3 = st.columns(3)
    total_gasto = df_f['VALOR_PAGO'].sum()
    c1.metric("💰 Total Gasto", f"R$ {total_gasto:,.2f}")
    c2.metric("👥 Funcionários", len(df_f[col_func].unique()))
    
    # Ajuste para mostrar o maior lançamento individual
    maior_lan = df_f['VALOR_PAGO'].max() if not df_f.empty else 0
    c3.metric("📈 Maior Valor", f"R$ {maior_lan:,.2f}")

    st.divider()
    
    # Gráfico de Barras - Top 10
    st.subheader("🏆 Maiores Custos por Funcionário")
    if not df_f.empty:
        top_10 = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        fig = px.bar(top_10, x='VALOR_PAGO', y=col_func, orientation='h', 
                     text_auto=',.2f', color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada formatada
    st.subheader("📑 Detalhamento")
    df_mostra = df_f.copy()
    if 'DATA_REF' in df_mostra.columns:
        df_mostra['DATA_REF'] = df_mostra['DATA_REF'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_mostra, use_container_width=True)

else:
    st.error("Arquivo não encontrado. Verifique o nome 'FUNCIONARIOS.csv' no seu GitHub.")
