"""
Teste simples do sistema sem emojis para compatibilidade Windows
"""

import sys
import os
import pandas as pd

# Adicionar diretório atual ao path
sys.path.append('.')

def test_imports():
    """Testa se os imports funcionam"""
    print("Testando imports...")
    try:
        from core import QuestionnaireProcessor, ScaleConverter
        from app_integration import filter_by_question_set, update_global_variables
        print("OK: Imports funcionando")
        return True
    except Exception as e:
        print(f"ERRO: Imports falharam - {str(e)}")
        return False

def test_configurations():
    """Testa se as configurações carregam"""
    print("Testando configuracoes...")
    try:
        from core import QuestionnaireProcessor
        processor = QuestionnaireProcessor()
        
        # Testar Base20
        config20 = processor.load_configuration("base20")
        print(f"OK: Base20 carregada - {len(config20['dimensions'])} dimensoes")
        
        # Testar Base8
        config8 = processor.load_configuration("base8")
        print(f"OK: Base8 carregada - {len(config8['dimensions'])} dimensoes")
        
        return True
    except Exception as e:
        print(f"ERRO: Configuracoes falharam - {str(e)}")
        return False

def test_scale_conversion():
    """Testa conversão de escalas"""
    print("Testando conversao de escalas...")
    try:
        from core import ScaleConverter
        converter = ScaleConverter()
        
        # Teste básico
        test_data = pd.Series(["Concordo", "Discordo", "Concordo Totalmente"])
        result = converter.convert_likert_column(test_data)
        
        if len(result) == len(test_data):
            print("OK: Conversao funcionando")
            return True
        else:
            print("ERRO: Resultado da conversao tem tamanho incorreto")
            return False
            
    except Exception as e:
        print(f"ERRO: Conversao falharam - {str(e)}")
        return False

def test_filters():
    """Testa filtros básicos"""
    print("Testando filtros...")
    try:
        from app_integration import filter_by_question_set, update_global_variables
        
        # Criar dados de teste
        test_data = pd.DataFrame({
            "O sistema e facil de usar.": [4, 5, 3],
            "As informacoes sao claras.": [5, 4, 4],
            "Sexo": ["M", "F", "M"],
            "Idade": [25, 30, 35]
        })
        
        # Testar filtro Base20
        update_global_variables("20 questoes")
        filtered = filter_by_question_set(test_data, "20 questoes")
        print(f"OK: Filtro Base20 - {len(filtered.columns)} colunas")
        
        # Testar filtro Base8
        update_global_variables("8 questoes")
        filtered = filter_by_question_set(test_data, "8 questoes")
        print(f"OK: Filtro Base8 - {len(filtered.columns)} colunas")
        
        return True
        
    except Exception as e:
        print(f"ERRO: Filtros falharam - {str(e)}")
        return False

def main():
    """Função principal"""
    print("TESTE SIMPLES DO SISTEMA")
    print("=" * 40)
    
    tests = [
        ("Imports", test_imports),
        ("Configuracoes", test_configurations),
        ("Conversao de Escalas", test_scale_conversion),
        ("Filtros", test_filters)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}...")
        try:
            if test_func():
                print(f"[PASS] {test_name}")
                passed += 1
            else:
                print(f"[FAIL] {test_name}")
        except Exception as e:
            print(f"[ERROR] {test_name} - {str(e)}")
    
    print("\n" + "=" * 40)
    print(f"RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("SUCESSO: Sistema funcionando corretamente!")
        return True
    else:
        print("FALHA: Sistema precisa de correcoes!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)