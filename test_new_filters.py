"""
Teste dos novos filtros: Base26, Base20 (com remoção de 6 questões), Base8

Este script testa se os filtros estão funcionando corretamente com a nova estrutura.
"""

import pandas as pd
import numpy as np
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append('.')

def create_test_dataset_with_all_questions():
    """Cria dataset de teste com todas as questões do Base26"""
    
    # Questões do Base26 (todas as 26 questões)
    base26_questions = [
        # Qualidade do Sistema (10 questões)
        "O sistema funciona sem falhas.",
        "Os recursos de acessibilidade do sistema são fáceis de encontrar.",  # SERÁ REMOVIDA no Base20
        "O sistema é fácil de usar.",
        "O sistema está disponível para uso em qualquer dia e hora.",
        "O desempenho do sistema é satisfatório, independentemente da forma de acesso.",
        "O sistema informa sobre as políticas de privacidade e segurança.",  # SERÁ REMOVIDA no Base20
        "Acredito que meus dados estão seguros neste sistema.",
        "É fácil localizar os serviços e as informações no sistema.",
        "A navegação pelo sistema é intuitiva.",
        "O sistema oferece instruções úteis de como utilizar os serviços.",  # SERÁ REMOVIDA no Base20
        
        # Qualidade da Informação (7 questões)
        "As informações são fáceis de entender.",
        "As informações são precisas.",
        "As informações auxiliam na solicitação dos serviços.",
        "Todas as informações necessárias para a solicitação dos serviços são fornecidas.",
        "O prazo de entrega dos serviços é informado.",  # SERÁ REMOVIDA no Base20
        "As taxas cobradas pelos serviços são informadas.",  # SERÁ REMOVIDA no Base20
        "As informações disponibilizadas estão atualizadas.",
        
        # Qualidade da Operação (9 questões)
        "Os serviços oferecem suporte técnico eficiente.",
        "O atendimento resolve meus problemas.",
        "Os serviços permitem a conclusão das tarefas no menor tempo possível.",
        "Consigo obter o que preciso no menor tempo possível.",
        "Os serviços atendem às minhas expectativas.",
        "Quando preciso de ajuda, minhas dificuldades são resolvidas.",
        "Meus dados são automaticamente identificados na solicitação dos serviços.",
        "Os serviços oferecidos são confiáveis.",
        "Os serviços permitem interações em tempo real (ex. chatbot, IA)."  # SERÁ REMOVIDA no Base20
    ]
    
    # Questões adicionais (não-questão)
    additional_columns = [
        "Qual o seu nível de satisfação com o Sistema?",
        "Qual o seu sexo?",
        "Qual a sua idade?",
        "Timestamp"
    ]
    
    all_columns = base26_questions + additional_columns
    
    # Criar dados de teste
    responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
    satisfaction_responses = ["Muito insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito satisfeito"]
    
    data = {}
    
    # Preencher questões com respostas Likert
    for question in base26_questions:
        data[question] = np.random.choice(responses, 10)
    
    # Preencher colunas adicionais
    data["Qual o seu nível de satisfação com o Sistema?"] = np.random.choice(satisfaction_responses, 10)
    data["Qual o seu sexo?"] = np.random.choice(["Masculino", "Feminino"], 10)
    data["Qual a sua idade?"] = np.random.choice(["18-25", "26-35", "36-45"], 10)
    data["Timestamp"] = pd.date_range("2024-01-01", periods=10)
    
    return pd.DataFrame(data)


def test_base26_filter():
    """Testa o filtro Base26 (completo)"""
    print("🔍 Testando filtro Base26 (Completo - 26 questões)...")
    
    try:
        from app_integration import app_integration
        
        # Criar dataset completo
        df = create_test_dataset_with_all_questions()
        print(f"   Dataset original: {len(df.columns)} colunas")
        
        # Aplicar filtro Base26
        filtered_df = app_integration.filter_by_question_set(df, "Completo (26 questões)")
        
        print(f"   ✅ Base26: {len(filtered_df.columns)} colunas mantidas")
        print(f"   ✅ Deve manter todas as colunas: {len(filtered_df.columns) == len(df.columns)}")
        
        return len(filtered_df.columns) == len(df.columns)
        
    except Exception as e:
        print(f"   ❌ Erro no teste Base26: {str(e)}")
        return False


def test_base20_filter():
    """Testa o filtro Base20 (remove 6 questões específicas)"""
    print("\n🔍 Testando filtro Base20 (20 questões - remove 6 específicas)...")
    
    try:
        from app_integration import app_integration
        
        # Criar dataset completo
        df = create_test_dataset_with_all_questions()
        print(f"   Dataset original: {len(df.columns)} colunas")
        
        # Questões que devem ser removidas
        questoes_removidas = [
            "Os recursos de acessibilidade do sistema são fáceis de encontrar.",
            "O sistema informa sobre as políticas de privacidade e segurança.",
            "O sistema oferece instruções úteis de como utilizar os serviços.",
            "O prazo de entrega dos serviços é informado.",
            "As taxas cobradas pelos serviços são informadas.",
            "Os serviços permitem interações em tempo real (ex. chatbot, IA)."
        ]
        
        # Aplicar filtro Base20
        filtered_df = app_integration.filter_by_question_set(df, "20 questões")
        
        print(f"   ✅ Base20: {len(filtered_df.columns)} colunas mantidas")
        print(f"   ✅ Deveria remover 6 questões: {len(df.columns) - len(filtered_df.columns)} removidas")
        
        # Verificar se as questões corretas foram removidas
        removed_correctly = True
        for questao in questoes_removidas:
            if questao in filtered_df.columns:
                print(f"   ❌ Questão não foi removida: {questao[:50]}...")
                removed_correctly = False
            else:
                print(f"   ✅ Questão removida corretamente: {questao[:50]}...")
        
        expected_columns = len(df.columns) - 6
        actual_columns = len(filtered_df.columns)
        
        return removed_correctly and (actual_columns == expected_columns)
        
    except Exception as e:
        print(f"   ❌ Erro no teste Base20: {str(e)}")
        return False


def test_base8_filter():
    """Testa o filtro Base8"""
    print("\n🔍 Testando filtro Base8 (8 questões)...")
    
    try:
        from app_integration import app_integration
        
        # Criar dataset completo
        df = create_test_dataset_with_all_questions()
        print(f"   Dataset original: {len(df.columns)} colunas")
        
        # Aplicar filtro Base8
        filtered_df = app_integration.filter_by_question_set(df, "8 questões")
        
        print(f"   ✅ Base8: {len(filtered_df.columns)} colunas mantidas")
        
        # Base8 deve remover muito mais colunas que Base20
        removed_count = len(df.columns) - len(filtered_df.columns)
        print(f"   ✅ Colunas removidas: {removed_count}")
        
        # Deve manter menos colunas que Base20
        return removed_count > 6  # Deve remover mais que as 6 do Base20
        
    except Exception as e:
        print(f"   ❌ Erro no teste Base8: {str(e)}")
        return False


def test_filter_progression():
    """Testa a progressão lógica dos filtros"""
    print("\n🔍 Testando progressão lógica dos filtros...")
    
    try:
        from app_integration import app_integration
        
        # Criar dataset completo
        df = create_test_dataset_with_all_questions()
        
        # Aplicar todos os filtros
        base26_df = app_integration.filter_by_question_set(df, "Completo (26 questões)")
        base20_df = app_integration.filter_by_question_set(df, "20 questões")
        base8_df = app_integration.filter_by_question_set(df, "8 questões")
        
        base26_cols = len(base26_df.columns)
        base20_cols = len(base20_df.columns)
        base8_cols = len(base8_df.columns)
        
        print(f"   Base26: {base26_cols} colunas")
        print(f"   Base20: {base20_cols} colunas")
        print(f"   Base8:  {base8_cols} colunas")
        
        # Verificar progressão lógica: Base26 > Base20 > Base8
        progression_correct = base26_cols > base20_cols > base8_cols
        
        if progression_correct:
            print("   ✅ Progressão correta: Base26 > Base20 > Base8")
        else:
            print("   ❌ Progressão incorreta")
        
        # Verificar diferenças específicas
        base26_to_base20_diff = base26_cols - base20_cols
        print(f"   ✅ Base26 → Base20: -{base26_to_base20_diff} colunas (esperado: -6)")
        
        return progression_correct and (base26_to_base20_diff == 6)
        
    except Exception as e:
        print(f"   ❌ Erro no teste de progressão: {str(e)}")
        return False


def test_configuration_updates():
    """Testa se as configurações são atualizadas corretamente"""
    print("\n🔍 Testando atualizações de configuração...")
    
    try:
        from app_integration import app_integration
        
        # Testar cada filtro
        filters_to_test = [
            "Completo (26 questões)",
            "20 questões", 
            "8 questões"
        ]
        
        for filter_name in filters_to_test:
            print(f"   🔄 Testando configuração: {filter_name}")
            
            try:
                app_integration.update_global_variables(filter_name)
                print(f"   ✅ Configuração atualizada para: {filter_name}")
            except Exception as e:
                print(f"   ❌ Erro na configuração {filter_name}: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro geral nas configurações: {str(e)}")
        return False


def run_new_filter_tests():
    """Executa todos os testes dos novos filtros"""
    print("🧪 Teste dos Novos Filtros: Base26, Base20, Base8")
    print("=" * 60)
    
    tests = [
        ("Filtro Base26 (Completo)", test_base26_filter),
        ("Filtro Base20 (Remove 6 questões)", test_base20_filter),
        ("Filtro Base8 (8 questões)", test_base8_filter),
        ("Progressão Lógica dos Filtros", test_filter_progression),
        ("Atualizações de Configuração", test_configuration_updates)
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
    print("📊 RESUMO DOS TESTES DOS NOVOS FILTROS:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES DOS NOVOS FILTROS PASSARAM!")
        print("\n✅ Estrutura implementada corretamente:")
        print("  • Base26 (Completo): 26 questões - mantém todas")
        print("  • Base20: 20 questões - remove 6 específicas do Base26")
        print("  • Base8: 8 questões - conjunto mínimo")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("  1. Execute: streamlit run app.py")
        print("  2. Teste os novos filtros na barra lateral")
        print("  3. Verifique se 'Completo (26 questões)' mantém tudo")
        print("  4. Verifique se '20 questões' remove as 6 questões corretas")
        print("  5. Observe as dimensões sendo reorganizadas")
        
        return True
    else:
        print(f"\n❌ {total - passed} TESTES FALHARAM!")
        print("\n🔧 CORREÇÕES NECESSÁRIAS:")
        
        for test_name, success in results:
            if not success:
                print(f"  • {test_name}")
        
        return False


if __name__ == "__main__":
    success = run_new_filter_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 NOVOS FILTROS FUNCIONANDO CORRETAMENTE!")
        print("\n📋 ESTRUTURA FINAL:")
        print("✅ Base26 (Completo): QS(10) + QI(7) + QO(9) = 26 questões")
        print("✅ Base20: Remove 6 questões específicas = 20 questões")
        print("✅ Base8: QS(4) + QI(3) + QO(1) = 8 questões")
        exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ CORREÇÕES NECESSÁRIAS NOS NOVOS FILTROS!")
        exit(1)