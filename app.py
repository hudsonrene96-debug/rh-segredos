import pandas as pd
import plotly.express as px
import streamlit as st
import io

# Configuração da página
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    file_path = 'FUNCIONARIOS.csv'
    # Lista de tentativas com diferentes configurações
    tentativas = [
        {'encoding': 'latin1', 'sep': None},
        {'encoding': 'iso-8859-1', 'sep': None},
        {'encoding': 'utf-8-sig', 'sep': None},
        {'encoding': 'cp1252', 'sep': None},
        {'encoding': 'utf-8', 'sep': ',', 'errors': 'ignore'}
    ]
    
    for config in tentativas:
        try:
            # Lemos o arquivo bruto primeiro para limpar caracteres estranhos
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Tentamos carregar o DataFrame
            df = pd.read_csv(io.BytesIO(content), 
                             sep=config.get('sep'), 
                             engine='python', 
                             encoding=config.get('encoding'),
                             on_bad_lines='skip')
            
            # Se o DF estiver vazio ou tiver apenas uma coluna estranha, tentamos a próxima
            if df.empty or len(df.columns) < 2:
                continue
                
            # Limpeza de nomes de colunas
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Conversão financeira segura
            if 'VLRDESDOB' in df.columns:
                df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Conversão de data (Excel)
            if 'DTNEG' in df.columns:
                df['DATA'] = pd.to_datetime(pd.to_numeric(df['DTNEG'], errors='coerce'), 
                                           unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except Exception:
            continue
            
    return None

df = carregar_dados()

if df is not None:
    st.title("👥 Gestão de RH - Bem Leve (Privado)")
    
    # Verificação de colunas para o filtro
    col_func = 'RAZAOSOCIAL'
    if col_func not in df.columns:
        # Se não achar RAZAOSOCIAL, tenta pegar a primeira coluna de texto
        col_func = df.select_dtypes(include=['object']).columns[0]

    st.sidebar.header("🔍 Filtros")
    lista_func = sorted(df[col_func].unique().astype(str))
    sel_func = st.sidebar.multiselect("Selecionar Funcionário(s):", options=lista_func)
    
    df_f = df[df[col_func].isin(sel_func)] if sel_func else df

    # Indicadores
    c1, c2 = st.columns(2)
    c1.metric("💰 Total Pago", f"R$ {df_f['VLRDESDOB'].sum():,.2f}")
    c2.metric("👥 Colaboradores", len(df_f[col_func].unique()))

    st.markdown("---")

    # Gráfico
    st.subheader("📊 Maiores Custos")
    rank = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
    fig = px.bar(rank, x='VLRDESDOB', y=col_func, orientation='h', color='VLRDESDOB')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📑 Dados Detalhados")
    st.dataframe(df_f, use_container_width=True)
else:
    st.error("Erro crítico: O arquivo 'FUNCIONARIOS.csv' não parece ser um CSV válido. Tente abrir o arquivo no Excel e 'Salvar Como' -> 'CSV (Separado por vírgulas)' e suba novamente ao GitHub.")
