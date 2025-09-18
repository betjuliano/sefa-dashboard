"""
Script para verificar a estrutura exata das dimensões nos arquivos de configuração
"""
import json
from pathlib import Path


def verify_dimensions():
    """Verifica a estrutura das dimensões nos arquivos de configuração"""
    
    print("=== Verificação da Estrutura das Dimensões ===\n")
    
    # Verificar Base20
    print("📊 BASE20 (items_mapping.json):")
    with open("config/items_mapping.json", 'r', encoding='utf-8') as f:
        base20_config = json.load(f)
    
    for dimension_name, questions in base20_config["dimensions"].items():
        print(f"  {dimension_name}: {len(questions)} questões")
        for i, question in enumerate(questions, 1):
            print(f"    {i}. {question}")
        print()
    
    # Verificar Base8
    print("📊 BASE8 (items_mapping_8q.json):")
    with open("config/items_mapping_8q.json", 'r', encoding='utf-8') as f:
        base8_config = json.load(f)
    
    for dimension_name, questions in base8_config["dimensions"].items():
        print(f"  {dimension_name}: {len(questions)} questões")
        for i, question in enumerate(questions, 1):
            print(f"    {i}. {question}")
        print()
    
    # Resumo
    print("📋 RESUMO:")
    print("Base20:")
    for dim_name, questions in base20_config["dimensions"].items():
        short_name = dim_name.split()[-1]  # Pega a última palavra
        print(f"  {short_name}: {len(questions)} questões")
    
    print("\nBase8:")
    for dim_name, questions in base8_config["dimensions"].items():
        short_name = dim_name.split()[-1]  # Pega a última palavra
        print(f"  {short_name}: {len(questions)} questões")


if __name__ == "__main__":
    verify_dimensions()