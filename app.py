import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página
st.set_page_config(page_title="RH Segredos | Bem Leve", layout="wide", page_icon="👥")

@st.cache_data
def carregar_dados():
    # Lista de codificações para testar (Excel BR costuma usar latin1)
    for encoding in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv('FUNCIONARIOS.csv', sep=None, engine='python', encoding=encoding)
            df.columns = [str(c).strip().upper() for c in df.columns]
            
            # Converter valores financeiros
            if 'VLRDESDOB' in df.columns:
                df['VLRDESDOB'] = pd.to_numeric(df['VLRDESDOB'], errors='coerce').fillna(0)
            
            # Converter datas (padrão Excel)
            if 'DTNEG' in df.columns:
                df['DATA'] = pd.to_datetime(df['DTNEG'], unit='D', origin='1899-12-30', errors='coerce')
            
            return df
        except Exception:
            continue
    
    st.error("Não foi possível ler o arquivo. Verifique se ele é um CSV válido.")
    return None

df = carregar_dados()

if df is not None:
    st.title("👥 Gestão de RH - Bem Leve (Privado)")
    
    # Filtros na Barra Lateral
    st.sidebar.header("🔍 Filtros de Consulta")
    col_func = 'RAZAOSOCIAL'
    
    if col_func in df.columns:
        lista_func = sorted(df[col_func].unique().astype(str))
        sel_func = st.sidebar.multiselect("Selecionar Funcionário(s):", options=lista_func)
        
        df_f = df[df[col_func].isin(sel_func)] if sel_func else df

        # Indicadores principais
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 Total Desembolsado", f"R$ {df_f['VLRDESDOB'].sum():,.2f}")
        m2.metric("👥 Qtd. Funcionários", len(df_f[col_func].unique()))
        m3.metric("📑 Total Lançamentos", len(df_f))

        st.markdown("---")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("📊 Top 10 Maiores Custos")
            rank = df_f.groupby(col_func)['VLRDESDOB'].sum().sort_values(ascending=True).tail(10).reset_index()
            fig1 = px.bar(rank, x='VLRDESDOB', y=col_func, orientation='h', color='VLRDESDOB', color_continuous_scale='Reds')
            st.plotly_chart(fig1, use_container_width=True)
        
        with g2:
            st.subheader("🍕 Distribuição por Histórico")
            if 'HISTORICO' in df_f.columns:
                hist_resumo = df_f.groupby('HISTORICO')['VLRDESDOB'].sum().sort_values(ascending=False).head(10).reset_index()
                fig2 = px.pie(hist_resumo, values='VLRDESDOB', names='HISTORICO', hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📑 Histórico Detalhado")
        # Formatar data para exibição
        df_display = df_f.copy()
        if 'DATA' in df_display.columns:
            df_display['DATA'] = df_display['DATA'].dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_display[[col_func, 'VLRDESDOB', 'HISTORICO', 'DATA']], use_container_width=True)
    else:
        st.error(f"Coluna '{col_func}' não encontrada. Colunas detectadas: {list(df.columns)}")
