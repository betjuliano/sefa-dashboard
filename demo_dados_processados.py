#!/usr/bin/env python3
"""
Demonstração de uso dos dados processados do basetransp.csv
Este script mostra como trabalhar com os dados já convertidos em valores numéricos.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def carregar_dados_processados():
    """Carrega os dados pré-processados"""
    try:
        df = pd.read_csv('data/basetransp_processado.csv', sep=';', encoding='latin-1')
        print(f"✅ Dados carregados com sucesso: {len(df)} linhas")
        return df
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return None

def analisar_estatisticas_basicas(df):
    """Análise estatística básica dos dados processados"""
    print("\n" + "="*50)
    print("📊 ESTATÍSTICAS BÁSICAS")
    print("="*50)
    
    # Estatísticas da média geral
    print(f"Média geral das respostas: {df['Media_Respostas'].mean():.2f}")
    print(f"Mediana: {df['Media_Respostas'].median():.2f}")
    print(f"Desvio padrão: {df['Media_Respostas'].std():.2f}")
    print(f"Valor mínimo: {df['Media_Respostas'].min():.2f}")
    print(f"Valor máximo: {df['Media_Respostas'].max():.2f}")
    
    # Distribuição de respostas válidas
    print(f"\n📈 Distribuição de respostas válidas por linha:")
    valid_counts = df['Num_Respostas_Validas'].value_counts().sort_index()
    for count, freq in valid_counts.items():
        print(f"  {count} respostas: {freq} linhas ({freq/len(df)*100:.1f}%)")

def analisar_por_questao(df):
    """Análise por questão individual"""
    print("\n" + "="*50)
    print("📋 ANÁLISE POR QUESTÃO")
    print("="*50)
    
    # Colunas das questões (excluindo as de controle)
    questoes = [col for col in df.columns if col not in ['Media_Respostas', 'Num_Respostas_Validas']]
    questoes = [col for col in questoes if not any(x in col.lower() for x in ['sexo', 'idade', 'escolaridade', 'funcionário', 'satisfação', 'comentários'])]
    
    medias_questoes = {}
    for questao in questoes:
        # Converter para numérico, ignorando valores não numéricos
        valores_numericos = pd.to_numeric(df[questao], errors='coerce')
        media = valores_numericos.mean()
        if not pd.isna(media):
            medias_questoes[questao] = media
    
    # Ordenar por média (do menor para o maior)
    medias_ordenadas = sorted(medias_questoes.items(), key=lambda x: x[1])
    
    print("Ranking das questões (da menor para a maior média):")
    for i, (questao, media) in enumerate(medias_ordenadas, 1):
        questao_curta = questao[:60] + "..." if len(questao) > 60 else questao
        status = "🔴" if media < 3.5 else "🟡" if media < 4.0 else "🟢"
        print(f"{i:2d}. {status} {questao_curta}")
        print(f"     Média: {media:.2f}")
        print()

def identificar_pontos_criticos(df, meta=4.0):
    """Identifica pontos críticos abaixo da meta"""
    print("\n" + "="*50)
    print(f"🚨 PONTOS CRÍTICOS (Meta: {meta})")
    print("="*50)
    
    questoes = [col for col in df.columns if col not in ['Media_Respostas', 'Num_Respostas_Validas']]
    questoes = [col for col in questoes if not any(x in col.lower() for x in ['sexo', 'idade', 'escolaridade', 'funcionário', 'satisfação', 'comentários'])]
    
    criticos = []
    for questao in questoes:
        valores_numericos = pd.to_numeric(df[questao], errors='coerce')
        media = valores_numericos.mean()
        if not pd.isna(media) and media < meta:
            gap = meta - media
            criticos.append((questao, media, gap))
    
    # Ordenar por gap (maior gap = mais crítico)
    criticos.sort(key=lambda x: x[2], reverse=True)
    
    if criticos:
        print(f"Encontrados {len(criticos)} pontos críticos:")
        for i, (questao, media, gap) in enumerate(criticos, 1):
            questao_curta = questao[:60] + "..." if len(questao) > 60 else questao
            print(f"{i:2d}. {questao_curta}")
            print(f"     Média: {media:.2f} | Gap: {gap:.2f}")
            print()
    else:
        print("🎉 Nenhum ponto crítico encontrado! Todas as questões estão acima da meta.")

def gerar_relatorio_completo(df):
    """Gera um relatório completo dos dados"""
    print("\n" + "="*70)
    print("📄 RELATÓRIO COMPLETO - DADOS PROCESSADOS")
    print("="*70)
    
    print(f"📊 Total de respostas analisadas: {len(df)}")
    print(f"📈 Média geral de satisfação: {df['Media_Respostas'].mean():.2f}")
    
    # Classificação por faixas
    excelente = len(df[df['Media_Respostas'] >= 4.5])
    bom = len(df[(df['Media_Respostas'] >= 4.0) & (df['Media_Respostas'] < 4.5)])
    regular = len(df[(df['Media_Respostas'] >= 3.0) & (df['Media_Respostas'] < 4.0)])
    ruim = len(df[df['Media_Respostas'] < 3.0])
    
    print(f"\n📊 Distribuição por faixas de satisfação:")
    print(f"  🟢 Excelente (4.5-5.0): {excelente} respostas ({excelente/len(df)*100:.1f}%)")
    print(f"  🔵 Bom (4.0-4.4): {bom} respostas ({bom/len(df)*100:.1f}%)")
    print(f"  🟡 Regular (3.0-3.9): {regular} respostas ({regular/len(df)*100:.1f}%)")
    print(f"  🔴 Ruim (<3.0): {ruim} respostas ({ruim/len(df)*100:.1f}%)")

def main():
    """Função principal"""
    print("🚀 ANÁLISE DOS DADOS PROCESSADOS - PORTAL DA TRANSPARÊNCIA")
    print("="*70)
    
    # Carregar dados
    df = carregar_dados_processados()
    if df is None:
        return
    
    # Executar análises
    analisar_estatisticas_basicas(df)
    analisar_por_questao(df)
    identificar_pontos_criticos(df, meta=4.0)
    gerar_relatorio_completo(df)
    
    print("\n" + "="*70)
    print("✅ Análise concluída!")
    print("💡 Os dados estão prontos para uso no dashboard Streamlit.")
    print("="*70)

if __name__ == "__main__":
    main()