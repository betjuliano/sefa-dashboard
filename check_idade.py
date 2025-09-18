import pandas as pd

# Verificar arquivo original
print("=== ARQUIVO ORIGINAL ===")
df_orig = pd.read_csv('sample_data/basetransp.csv', sep=';', encoding='latin-1')
print(f"Total de linhas: {len(df_orig)}")
print(f"Total de colunas: {len(df_orig.columns)}")

# Procurar colunas com 'idade'
idade_cols = [col for col in df_orig.columns if 'idade' in col.lower()]
print(f"Colunas com 'idade': {idade_cols}")

if idade_cols:
    col_idade = idade_cols[0]
    print(f"Valores únicos na coluna '{col_idade}':")
    print(df_orig[col_idade].unique()[:20])
    print(f"Total de valores únicos: {df_orig[col_idade].nunique()}")
    print(f"Valores nulos: {df_orig[col_idade].isnull().sum()}")

print("\n=== ARQUIVO PROCESSADO ===")
df_proc = pd.read_csv('data/basetransp_processado.csv', sep=';', encoding='latin-1')
print(f"Total de linhas: {len(df_proc)}")
print(f"Total de colunas: {len(df_proc.columns)}")

# Procurar colunas com 'idade'
idade_cols_proc = [col for col in df_proc.columns if 'idade' in col.lower()]
print(f"Colunas com 'idade': {idade_cols_proc}")

if idade_cols_proc:
    col_idade_proc = idade_cols_proc[0]
    print(f"Valores únicos na coluna '{col_idade_proc}':")
    print(df_proc[col_idade_proc].unique()[:20])
    print(f"Total de valores únicos: {df_proc[col_idade_proc].nunique()}")
    print(f"Valores nulos: {df_proc[col_idade_proc].isnull().sum()}")