@st.cache_data
def carregar_dados():
    import os
    # Isso vai nos mostrar se o arquivo realmente existe na pasta
    arquivos_na_pasta = os.listdir('.')
    
    file_path = 'FUNCIONARIOS.csv'
    
    if file_path not in arquivos_na_pasta:
        st.error(f"Arquivo não encontrado! Arquivos detectados na pasta: {arquivos_na_pasta}")
        return None

    for enc in ['latin1', 'iso-8859-1', 'utf-8-sig', 'cp1252']:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', encoding=enc)
            df.columns = [str(c).strip().upper() for c in df.columns]
            # ... resto do seu código de tratamento ...
            return df
        except:
            continue
    return None
