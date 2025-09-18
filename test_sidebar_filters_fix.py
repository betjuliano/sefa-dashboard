"""
Teste específico para verificar se os filtros da barra lateral estão funcionando

Este script testa especificamente os problemas identificados nos filtros.
"""

import pandas as pd
import numpy as np
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append('.')

def test_filter_functions():
    """Testa se as funções de filtro estão funcionando"""
    print("🔍 Testando funções de filtro...")
    
    try:
        from app_integration import (
            app_integration,
            update_global_variables,
            filter_by_question_set
        )
        
        # Criar dataset de teste
        test_data = pd.DataFrame({
            "O sistema é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "As informações são claras.": ["Concordo", "Concordo"],
            "Consigo obter o que preciso no menor tempo possível.": ["Indiferente", "Concordo"],
            "O Portal é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "Qual o seu sexo?": ["Masculino", "Feminino"],
            "Timestamp": pd.date_range("2024-01-01", periods=2)
        })
        
        print(f"✅ Dataset de teste criado: {len(test_data)} linhas, {len(test_data.columns)} colunas")
        
        # Testar cada filtro
        for question_set in ["Completo", "20 questões", "8 questões"]:
            print(f"\n🔄 Testando filtro: {question_set}")
            
            try:
                # Atualizar variáveis globais
                update_global_variables(question_set)
                print(f"  ✅ Variáveis globais atualizadas para {question_set}")
                
                # Aplicar filtro
                filtered_data = filter_by_question_set(test_data, question_set)
                print(f"  ✅ Filtro aplicado: {len(filtered_data.columns)} colunas resultantes")
                
                # Verificar se o resultado é válido
                if len(filtered_data) > 0 and len(filtered_data.columns) > 0:
                    print(f"  ✅ Resultado válido: {len(filtered_data)} linhas, {len(filtered_data.columns)} colunas")
                else:
                    print(f"  ❌ Resultado inválido: dataset vazio")
                    return False
                
            except Exception as e:
                print(f"  ❌ Erro no filtro {question_set}: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral nos testes de filtro: {str(e)}")
        return False


def test_configuration_loading():
    """Testa se as configurações estão sendo carregadas corretamente"""
    print("\n🔍 Testando carregamento de configurações...")
    
    try:
        from app_integration import app_integration
        
        # Testar cada configuração
        for question_set, internal_name in [("Completo", "base20"), ("20 questões", "base20"), ("8 questões", "base8")]:
            print(f"\n🔄 Testando configuração: {question_set} -> {internal_name}")
            
            try:
                config = app_integration.processor.load_configuration(internal_name)
                
                # Verificar estrutura da configuração
                required_keys = ["dimensions", "likert_map", "satisfaction_field", "profile_fields"]
                for key in required_keys:
                    if key not in config:
                        print(f"  ❌ Chave '{key}' não encontrada na configuração")
                        return False
                
                print(f"  ✅ Configuração válida: {len(config['dimensions'])} dimensões")
                
                # Verificar dimensões
                for dim_name, questions in config["dimensions"].items():
                    print(f"    • {dim_name}: {len(questions)} questões")
                
            except Exception as e:
                print(f"  ❌ Erro ao carregar configuração {question_set}: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral no carregamento de configurações: {str(e)}")
        return False


def test_global_variables_update():
    """Testa se as variáveis globais estão sendo atualizadas corretamente"""
    print("\n🔍 Testando atualização de variáveis globais...")
    
    try:
        from app_integration import update_global_variables
        import app
        
        # Testar cada conjunto de questões
        for question_set in ["Completo", "20 questões", "8 questões"]:
            print(f"\n🔄 Testando variáveis globais para: {question_set}")
            
            try:
                # Atualizar variáveis
                update_global_variables(question_set)
                
                # Verificar se as variáveis foram atualizadas
                required_vars = ["MAPPING", "DIMENSIONS", "LIKERT_MAP", "SAT_FIELD", "PROFILE_FIELDS"]
                for var_name in required_vars:
                    if not hasattr(app, var_name):
                        print(f"  ❌ Variável '{var_name}' não encontrada no app")
                        return False
                    
                    var_value = getattr(app, var_name)
                    if var_value is None:
                        print(f"  ❌ Variável '{var_name}' é None")
                        return False
                
                print(f"  ✅ Todas as variáveis globais atualizadas corretamente")
                print(f"    • Dimensões: {len(app.DIMENSIONS)}")
                print(f"    • Mapeamento Likert: {len(app.LIKERT_MAP)} itens")
                
            except Exception as e:
                print(f"  ❌ Erro ao atualizar variáveis para {question_set}: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro geral na atualização de variáveis globais: {str(e)}")
        return False


def test_streamlit_compatibility():
    """Testa compatibilidade com Streamlit (sem executar Streamlit)"""
    print("\n🔍 Testando compatibilidade com Streamlit...")
    
    try:
        # Simular session_state
        class MockSessionState:
            def __init__(self):
                self.question_set = "Completo"
                self.removed_columns = {}
        
        # Simular st.session_state
        import streamlit as st
        if not hasattr(st, 'session_state'):
            st.session_state = MockSessionState()
        
        from app_integration import app_integration
        
        # Testar funções que usam session_state
        try:
            stats = app_integration.get_processing_stats()
            print(f"  ✅ Estatísticas de processamento obtidas: {len(stats)} campos")
            
            # Testar cache
            app_integration.clear_cache()
            print(f"  ✅ Cache limpo com sucesso")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Erro na compatibilidade com Streamlit: {str(e)}")
            return False
        
    except Exception as e:
        print(f"❌ Erro geral na compatibilidade com Streamlit: {str(e)}")
        return False


def test_app_py_integration():
    """Testa se o app.py foi integrado corretamente"""
    print("\n🔍 Testando integração com app.py...")
    
    try:
        # Verificar se app.py existe e foi modificado
        if not os.path.exists("app.py"):
            print("❌ app.py não encontrado")
            return False
        
        with open("app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
        
        # Verificar se as modificações estão presentes
        checks = [
            ("Imports do novo sistema", "from app_integration import"),
            ("Função update_global_variables modificada", "NOVO SISTEMA"),
            ("Melhorias da barra lateral", "add_sidebar_enhancements"),
            ("Função normalize_likert modificada", "new_normalize_likert"),
            ("Função filter_by_question_set modificada", "new_filter_by_question_set")
        ]
        
        for check_name, check_text in checks:
            if check_text in app_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - não encontrado")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na verificação de integração do app.py: {str(e)}")
        return False


def run_sidebar_filter_tests():
    """Executa todos os testes específicos dos filtros da barra lateral"""
    print("🧪 Teste Específico dos Filtros da Barra Lateral")
    print("=" * 60)
    
    tests = [
        ("Funções de Filtro", test_filter_functions),
        ("Carregamento de Configurações", test_configuration_loading),
        ("Atualização de Variáveis Globais", test_global_variables_update),
        ("Compatibilidade com Streamlit", test_streamlit_compatibility),
        ("Integração com app.py", test_app_py_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES DOS FILTROS:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES DOS FILTROS PASSARAM!")
        print("✅ Os filtros da barra lateral estão funcionando corretamente!")
        return True
    else:
        print(f"\n❌ {total - passed} TESTES FALHARAM!")
        print("🔧 Os filtros da barra lateral precisam de correções!")
        return False


if __name__ == "__main__":
    success = run_sidebar_filter_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 FILTROS DA BARRA LATERAL FUNCIONANDO!")
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("  1. Execute: streamlit run app.py")
        print("  2. Teste os filtros manualmente")
        print("  3. Verifique se as dimensões são reorganizadas")
        exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ FILTROS PRECISAM DE CORREÇÕES!")
        print("\n🔧 AÇÕES NECESSÁRIAS:")
        print("  1. Corrija os problemas identificados")
        print("  2. Execute este teste novamente")
        print("  3. Teste manualmente após correções")
        exit(1)