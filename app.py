import pandas as pd
import plotly.express as px
import streamlit as st
import os

# Configuração da página
st.set_page_config(page_title="RH Estratégico | Bem Leve", layout="wide", page_icon="📊")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    
    # Verifica se o arquivo existe fisicamente na pasta
    if not os.path.exists(file_path):
        st.error(f"Arquivo '{file_path}' não encontrado no GitHub. Verifique o nome!")
        return None

    # Tenta várias codificações para resolver o erro de 'utf-8'
    for enc in ['latin1', 'iso-8859-1', 'cp1252', 'utf-8-sig']:
        try:
            # Tenta detectar o separador automaticamente (vírgula ou ponto e vírgula)
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            
            # Limpa nomes de colunas (remove espaços e coloca em maiúsculo)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Tratamento Financeiro (VLRDESDOB)
            col_vlr = next((c for c in df.columns if 'VLR' in c or 'VALOR' in c), None)
            if col_vlr:
                df['VALOR_PAGO'] = pd.to_numeric(df[col_vlr].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Tratamento de Data (DTNEG)
            if 'DTNEG' in df.columns:
                df['DATA_REF'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), unit='D', origin='1899-12-30', errors='coerce')
                df = df.dropna(subset=['DATA_REF'])
            
            return df
        except Exception as e:
            continue
    
    st.error("Não foi possível ler o arquivo com nenhuma codificação conhecida.")
    return None

df = carregar_dados()

# Só executa se os dados forem carregados com sucesso
if df is not None and not df.empty:
    st.title("📊 BI de Recursos Humanos - Bem Leve")
    
    # Mapeamento de Colunas
    col_emp = 'CODEMP' if 'CODEMP' in df.columns else df.columns[0]
    col_hist = 'HISTORICO' if 'HISTORICO' in df.columns else None
    col_func = 'RAZAOSOCIAL' if 'RAZAOSOCIAL' in df.columns else df.columns[1]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # Prevenção de NameError para a variável periodo
    periodo = None
    if 'DATA_REF' in df.columns:
        min_d, max_d = df['DATA_REF'].min().date(), df['DATA_REF'].max().date()
        periodo = st.sidebar.date_input("Período (DTNEG):", value=(min_d, max_d))

    sel_emp = st.sidebar.multiselect("Empresa (CODEMP):", options=sorted(df[col_emp].unique().astype(str)))
    
    # Filtro Histórico com proteção contra erro de ordenação
    opcoes_hist = sorted(df[col_hist].dropna().unique().astype(str)) if col_hist else []
    sel_hist = st.sidebar.multiselect("Natureza/Histórico:", options=opcoes_hist)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df.copy()
    
    if periodo and isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        df_f = df_f[(df_f['DATA_REF'].dt.date >= periodo[0]) & (df_f['DATA_REF'].dt.date <= periodo[1])]
    
    if sel_emp:  df_f = df_f[df_f[col_emp].astype(str).isin(sel_emp)]
    if sel_hist: df_f = df_f[df_f[col_hist].astype(str).isin(sel_hist)]

    # --- INDICADORES ---
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Total Gasto", f"R$ {df_f['VALOR_PAGO'].sum():,.2f}")
    c2.metric("👥 Qtd Funcionários", len(df_f[col_func].unique()))
    c3.metric("📈 Maior Valor", f"R$ {df_f['VALOR_PAGO'].max():,.2f}" if not df_f.empty else "R$ 0,00")

    # --- GRÁFICOS ---
    st.markdown("---")
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("🏆 Maiores Custos")
        rank = df_f.groupby(col_func)['VALOR_PAGO'].sum().sort_values(ascending=True).tail(10).reset_index()
        st.plotly_chart(px.bar(rank, x='VALOR_PAGO', y=col_func, orientation='h', color='VALOR_PAGO'), use_container_width=True)
        
    with g2:
        st.subheader("🍕 Distribuição")
        if col_hist and not df_f.empty:
            df_p = df_f.groupby(col_hist)['VALOR_PAGO'].sum().reset_index()
            st.plotly_chart(px.pie(df_p, values='VALOR_PAGO', names=col_hist, hole=0.4), use_container_width=True)

    st.subheader("📑 Detalhamento")
    st.dataframe(df_f, use_container_width=True)

else:
    # Caso o arquivo não seja encontrado ou esteja vazio
    st.info("Aguardando carregamento correto do arquivo 'FUNCIONARIOS.csv'...")
