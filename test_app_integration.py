"""
Teste da integração do novo sistema com o app.py

Este script testa se a integração foi aplicada corretamente e se todas as
funcionalidades estão funcionando como esperado.
"""

import pandas as pd
import numpy as np
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append('.')

def test_imports():
    """Testa se todos os imports necessários funcionam"""
    print("🔍 Testando imports...")
    
    try:
        from app_integration import (
            app_integration,
            update_global_variables,
            filter_by_question_set,
            compute_metrics,
            normalize_likert,
            normalize_satisfaction
        )
        print("✅ Imports da integração funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False


def test_core_system():
    """Testa se o sistema core está funcionando"""
    print("\n🔍 Testando sistema core...")
    
    try:
        from core import QuestionnaireProcessor, ScaleConverter, TextNormalizer
        
        processor = QuestionnaireProcessor()
        scale_converter = ScaleConverter()
        text_normalizer = TextNormalizer()
        
        print("✅ Sistema core funcionando")
        return True
    except Exception as e:
        print(f"❌ Erro no sistema core: {e}")
        return False


def test_configuration_loading():
    """Testa carregamento de configurações"""
    print("\n🔍 Testando carregamento de configurações...")
    
    try:
        from app_integration import app_integration
        
        # Testar base20
        config_base20 = app_integration.processor.load_configuration("base20")
        print(f"✅ Base20 carregada: {len(config_base20['dimensions'])} dimensões")
        
        # Testar base8
        config_base8 = app_integration.processor.load_configuration("base8")
        print(f"✅ Base8 carregada: {len(config_base8['dimensions'])} dimensões")
        
        return True
    except Exception as e:
        print(f"❌ Erro no carregamento de configurações: {e}")
        return False


def test_scale_conversion():
    """Testa conversão de escalas"""
    print("\n🔍 Testando conversão de escalas...")
    
    try:
        from app_integration import normalize_likert, normalize_satisfaction
        
        # Testar Likert
        likert_data = pd.Series([
            "Concordo totalmente",
            "Concordo", 
            "Indiferente",
            "Discordo",
            "Discordo totalmente"
        ])
        
        likert_result = normalize_likert(likert_data)
        expected_likert = [5, 4, 3, 2, 1]
        
        if likert_result.tolist() == expected_likert:
            print("✅ Conversão Likert funcionando")
        else:
            print(f"❌ Conversão Likert incorreta: {likert_result.tolist()} != {expected_likert}")
            return False
        
        # Testar Satisfação
        satisfaction_data = pd.Series([
            "Muito satisfeito",
            "Satisfeito",
            "Indiferente", 
            "Insatisfeito",
            "Muito insatisfeito"
        ])
        
        satisfaction_result = normalize_satisfaction(satisfaction_data)
        expected_satisfaction = [5, 4, 3, 2, 1]
        
        if satisfaction_result.tolist() == expected_satisfaction:
            print("✅ Conversão de satisfação funcionando")
        else:
            print(f"❌ Conversão de satisfação incorreta: {satisfaction_result.tolist()} != {expected_satisfaction}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erro na conversão de escalas: {e}")
        return False


def test_filtering():
    """Testa filtragem por conjunto de questões"""
    print("\n🔍 Testando filtragem por conjunto...")
    
    try:
        from app_integration import filter_by_question_set
        
        # Criar dataset de teste
        test_data = pd.DataFrame({
            "O sistema é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "As informações são claras.": ["Concordo", "Concordo"],
            "Consigo obter o que preciso no menor tempo possível.": ["Indiferente", "Concordo"],
            "Qual o seu sexo?": ["Masculino", "Feminino"],
            "Timestamp": pd.date_range("2024-01-01", periods=2)
        })
        
        # Testar filtro base20
        filtered_base20 = filter_by_question_set(test_data, "20 questões")
        print(f"✅ Filtro base20: {len(filtered_base20.columns)} colunas")
        
        # Testar filtro base8
        filtered_base8 = filter_by_question_set(test_data, "8 questões")
        print(f"✅ Filtro base8: {len(filtered_base8.columns)} colunas")
        
        return True
    except Exception as e:
        print(f"❌ Erro na filtragem: {e}")
        return False


def test_metrics_computation():
    """Testa cálculo de métricas"""
    print("\n🔍 Testando cálculo de métricas...")
    
    try:
        from app_integration import compute_metrics
        
        # Criar dataset de teste
        test_data = pd.DataFrame({
            "O sistema é fácil de usar.": [
                "Concordo totalmente", "Concordo", "Indiferente", 
                "Concordo", "Concordo totalmente"
            ],
            "As informações são claras.": [
                "Concordo", "Concordo totalmente", "Concordo",
                "Indiferente", "Concordo"
            ],
            "Consigo obter o que preciso no menor tempo possível.": [
                "Concordo", "Concordo", "Indiferente",
                "Discordo", "Concordo"
            ],
            "Qual o seu nível de satisfação com o Sistema?": [
                "Muito satisfeito", "Satisfeito", "Satisfeito",
                "Indiferente", "Muito satisfeito"
            ]
        })
        
        # Calcular métricas
        results = compute_metrics(test_data, 4.0)
        
        # Verificar estrutura dos resultados
        required_keys = ["items", "dimensions", "satisfaction", "insights"]
        for key in required_keys:
            if key not in results:
                print(f"❌ Chave '{key}' não encontrada nos resultados")
                return False
        
        print(f"✅ Métricas calculadas: {len(results['items'])} itens, {len(results['dimensions'])} dimensões")
        
        # Verificar se há insights
        total_insights = sum(len(results['insights'][category]) for category in results['insights'])
        print(f"✅ Insights gerados: {total_insights} itens classificados")
        
        return True
    except Exception as e:
        print(f"❌ Erro no cálculo de métricas: {e}")
        return False


def test_app_compatibility():
    """Testa compatibilidade com app.py"""
    print("\n🔍 Testando compatibilidade com app.py...")
    
    try:
        # Verificar se app.py foi modificado corretamente
        with open("app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
        
        # Verificar se imports foram adicionados
        if "from app_integration import" in app_content:
            print("✅ Imports do novo sistema encontrados no app.py")
        else:
            print("❌ Imports do novo sistema não encontrados no app.py")
            return False
        
        # Verificar se funções foram substituídas
        if "NOVO SISTEMA" in app_content:
            print("✅ Funções do novo sistema encontradas no app.py")
        else:
            print("❌ Funções do novo sistema não encontradas no app.py")
            return False
        
        # Verificar se melhorias da barra lateral foram adicionadas
        if "add_sidebar_enhancements" in app_content:
            print("✅ Melhorias da barra lateral encontradas no app.py")
        else:
            print("❌ Melhorias da barra lateral não encontradas no app.py")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erro na verificação de compatibilidade: {e}")
        return False


def test_performance():
    """Testa performance do novo sistema"""
    print("\n🔍 Testando performance...")
    
    try:
        import time
        from app_integration import compute_metrics
        
        # Criar dataset maior para teste de performance
        n_responses = 1000
        responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
        
        large_data = pd.DataFrame({
            "O sistema é fácil de usar.": np.random.choice(responses, n_responses),
            "As informações são claras.": np.random.choice(responses, n_responses),
            "Os serviços atendem às expectativas.": np.random.choice(responses, n_responses),
        })
        
        # Medir tempo de processamento
        start_time = time.time()
        results = compute_metrics(large_data, 4.0)
        end_time = time.time()
        
        processing_time = end_time - start_time
        rate = n_responses / processing_time
        
        print(f"✅ Performance: {processing_time:.3f}s para {n_responses:,} respostas")
        print(f"✅ Taxa: {rate:,.0f} respostas/segundo")
        
        # Verificar se o cache está funcionando
        start_time = time.time()
        results2 = compute_metrics(large_data, 4.0)  # Deve usar cache
        end_time = time.time()
        
        cache_time = end_time - start_time
        if cache_time < processing_time / 2:
            print(f"✅ Cache funcionando: {cache_time:.3f}s (2ª execução)")
        else:
            print(f"⚠️ Cache pode não estar funcionando: {cache_time:.3f}s")
        
        return True
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("🧪 Teste de Integração do Novo Sistema")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Sistema Core", test_core_system),
        ("Carregamento de Configurações", test_configuration_loading),
        ("Conversão de Escalas", test_scale_conversion),
        ("Filtragem", test_filtering),
        ("Cálculo de Métricas", test_metrics_computation),
        ("Compatibilidade com app.py", test_app_compatibility),
        ("Performance", test_performance)
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
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✅ A integração foi aplicada com sucesso!")
        print("✅ O novo sistema está funcionando corretamente!")
        print("✅ O app.py está pronto para uso!")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("  1. Execute: streamlit run app.py")
        print("  2. Teste os filtros da barra lateral")
        print("  3. Verifique as validações de estrutura")
        print("  4. Observe as melhorias de performance")
        print("  5. Use as novas funcionalidades de debug")
        
        return True
    else:
        print(f"\n❌ {total - passed} TESTES FALHARAM!")
        print("\n🔧 AÇÕES NECESSÁRIAS:")
        print("  1. Verifique os erros reportados acima")
        print("  2. Corrija os problemas identificados")
        print("  3. Execute os testes novamente")
        
        return False


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("🎯 INTEGRAÇÃO COMPLETA E FUNCIONAL!")
        exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ INTEGRAÇÃO INCOMPLETA - CORREÇÕES NECESSÁRIAS")
        exit(1)