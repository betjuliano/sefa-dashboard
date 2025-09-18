#!/usr/bin/env python3
"""
Script para pré-processar o arquivo basetransp.csv
Converte respostas Likert em valores numéricos e calcula médias por linha
"""

import os
import pandas as pd
import numpy as np
import json

def load_mapping():
    """Carrega o mapeamento de configuração"""
    with open(os.path.join("config", "items_mapping.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_likert_value(value, likert_map):
    """Converte um valor Likert individual em numérico"""
    if pd.isna(value) or value == "" or value is None:
        return np.nan
    
    # Limpar o valor (remover espaços extras)
    value = str(value).strip()
    
    # Mapear para valor numérico
    return likert_map.get(value, np.nan)

def preprocess_basetransp():
    """Processa o arquivo basetransp.csv"""
    
    # Carregar configurações
    mapping = load_mapping()
    
    # Obter mapeamento para 8 questões
    if "8 questões" in mapping:
        config_8q = mapping["8 questões"]
        dimensions = config_8q["dimensions"]
        likert_map = config_8q["likert_map"]
    else:
        # Fallback para configuração padrão
        dimensions = mapping["dimensions"]
        likert_map = mapping["likert_map"]
    
    print("📊 Mapeamento Likert:")
    for key, value in likert_map.items():
        print(f"  {key} → {value}")
    print()
    
    # Carregar arquivo original
    input_file = os.path.join("data", "basetransp.csv")
    if not os.path.exists(input_file):
        input_file = os.path.join("sample_data", "basetransp.csv")
    
    print(f"📂 Carregando arquivo: {input_file}")
    
    try:
        df = pd.read_csv(input_file, sep=";", encoding="latin-1")
        print(f"✅ Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return
    
    # Mostrar primeiras linhas originais
    print("\n📋 Primeiras 3 linhas originais:")
    print(df.head(3).to_string())
    
    # Identificar colunas de questões e colunas de perfil
    profile_fields = ["Idade", "Escolaridade", "Renda", "Sexo", "Satisfação"]
    question_columns = []
    profile_columns = []
    
    for col in df.columns:
        if col in profile_fields:
            profile_columns.append(col)
        else:
            # Verificar se contém respostas Likert
            unique_vals = df[col].dropna().unique()
            likert_found = any(str(val).strip() in likert_map for val in unique_vals if pd.notna(val))
            if likert_found:
                question_columns.append(col)
            else:
                profile_columns.append(col)
    
    print(f"\n🔍 Colunas de questões identificadas: {len(question_columns)}")
    for i, col in enumerate(question_columns, 1):
        print(f"  {i}. {col}")
    
    print(f"\n👤 Colunas de perfil identificadas: {len(profile_columns)}")
    for i, col in enumerate(profile_columns, 1):
        print(f"  {i}. {col}")
    
    # Criar DataFrame processado
    df_processed = df.copy()
    
    # Converter cada coluna de questão
    print("\n🔄 Convertendo respostas Likert para valores numéricos...")
    conversion_stats = {}
    
    for col in question_columns:
        if col in df.columns:
            original_values = df[col].value_counts(dropna=False)
            print(f"\n📊 Coluna: {col}")
            print("  Valores originais:")
            for val, count in original_values.items():
                print(f"    {val}: {count}")
            
            # Aplicar conversão
            df_processed[col] = df[col].apply(lambda x: normalize_likert_value(x, likert_map))
            
            # Estatísticas da conversão
            converted_values = df_processed[col].value_counts(dropna=False)
            print("  Valores convertidos:")
            for val, count in converted_values.items():
                print(f"    {val}: {count}")
            
            conversion_stats[col] = {
                'original_unique': len(original_values),
                'converted_unique': len(converted_values),
                'null_count': df_processed[col].isna().sum()
            }
    
    # Mostrar estatísticas dos dados de perfil preservados
    print(f"\n👤 Resumo dos dados de perfil preservados:")
    for col in profile_columns:
        if col in df_processed.columns:
            non_null = df_processed[col].count()
            total = len(df_processed)
            print(f"  - {col}: {non_null}/{total} valores não-nulos ({non_null/total*100:.1f}%)")
    
    # Calcular médias por linha (apenas para colunas de questões)
    print("\n📈 Calculando médias por linha...")
    numeric_columns = [col for col in question_columns if col in df_processed.columns]
    
    # Calcular média ignorando valores NaN
    df_processed['Media_Respostas'] = df_processed[numeric_columns].mean(axis=1, skipna=True)
    
    # Calcular número de respostas válidas por linha
    df_processed['Num_Respostas_Validas'] = df_processed[numeric_columns].notna().sum(axis=1)
    
    # Mostrar estatísticas das médias
    print(f"📊 Estatísticas das médias calculadas:")
    print(f"  Média geral: {df_processed['Media_Respostas'].mean():.2f}")
    print(f"  Mediana: {df_processed['Media_Respostas'].median():.2f}")
    print(f"  Desvio padrão: {df_processed['Media_Respostas'].std():.2f}")
    print(f"  Mínimo: {df_processed['Media_Respostas'].min():.2f}")
    print(f"  Máximo: {df_processed['Media_Respostas'].max():.2f}")
    
    # Mostrar distribuição de respostas válidas
    print(f"\n📊 Distribuição de respostas válidas por linha:")
    valid_counts = df_processed['Num_Respostas_Validas'].value_counts().sort_index()
    for count, freq in valid_counts.items():
        print(f"  {count} respostas: {freq} linhas")
    
    # Mostrar primeiras linhas processadas
    print("\n📋 Primeiras 3 linhas processadas:")
    display_cols = numeric_columns[:3] + profile_columns[:2] + ['Media_Respostas', 'Num_Respostas_Validas']
    # Filtrar apenas colunas que existem
    display_cols = [col for col in display_cols if col in df_processed.columns]
    print(df_processed[display_cols].head(3).to_string())
    
    # Salvar arquivo processado
    output_file = os.path.join("data", "basetransp_processado.csv")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        df_processed.to_csv(output_file, sep=";", encoding="latin-1", index=False)
        print(f"\n✅ Arquivo processado salvo: {output_file}")
        print(f"   Linhas: {len(df_processed)}, Colunas: {len(df_processed.columns)}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return
    
    # Criar relatório de conversão
    print("\n📋 Relatório de Conversão:")
    print("=" * 50)
    for col, stats in conversion_stats.items():
        print(f"Coluna: {col}")
        print(f"  Valores únicos originais: {stats['original_unique']}")
        print(f"  Valores únicos convertidos: {stats['converted_unique']}")
        print(f"  Valores nulos: {stats['null_count']}")
        print()
    
    print("🎉 Processamento concluído com sucesso!")
    print(f"📁 Arquivo original: {input_file}")
    print(f"📁 Arquivo processado: {output_file}")

if __name__ == "__main__":
    preprocess_basetransp()