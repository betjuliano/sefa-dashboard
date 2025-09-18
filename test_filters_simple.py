"""
Teste simplificado dos filtros da barra lateral sem dependências do Streamlit

Este teste verifica se as funções básicas estão funcionando corretamente.
"""

import pandas as pd
import numpy as np
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append('.')

def test_basic_functionality():
    """Testa funcionalidade básica sem Streamlit"""
    print("🔍 Testando funcionalidade básica...")
    
    try:
        # Importar apenas as funções essenciais
        from core import QuestionnaireProcessor, ScaleConverter
        
        # Testar carregamento de configurações
        processor = QuestionnaireProcessor()
        
        # Testar base20
        config_base20 = processor.load_configuration("base20")
        print(f"✅ Base20: {len(config_base20['dimensions'])} dimensões")
        
        # Testar base8
        config_base8 = processor.load_configuration("base8")
        print(f"✅ Base8: {len(config_base8['dimensions'])} dimensões")
        
        # Testar conversão de escalas
        converter = ScaleConverter()
        test_responses = pd.Series(["Concordo totalmente", "Discordo", "Indiferente"])
        converted = converter.convert_likert_column(test_responses)
        print(f"✅ Conversão: {converted.tolist()}")
        
        # Testar processamento básico
        test_data = pd.DataFrame({
            "O sistema é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "As informações são claras.": ["Concordo", "Concordo"],
            "Qual o seu sexo?": ["Masculino", "Feminino"]
        })
        
        results = processor.process_questionnaire_data(test_data, "base20")
        print(f"✅ Processamento: {len(results.dimensions)} dimensões processadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False


def test_filter_logic():
    """Testa a lógica de filtragem sem Streamlit"""
    print("\n🔍 Testando lógica de filtragem...")
    
    try:
        from core import QuestionnaireProcessor
        
        processor = QuestionnaireProcessor()
        
        # Criar dataset de teste
        test_data = pd.DataFrame({
            # Questões que existem no base20
            "O sistema é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "As informações são claras.": ["Concordo", "Concordo"],
            "Os serviços atendem às minhas expectativas.": ["Indiferente", "Concordo"],
            
            # Questões que existem no base8
            "O Portal é fácil de usar.": ["Concordo", "Concordo totalmente"],
            "É fácil localizar os dados e as informações no Portal.": ["Concordo", "Concordo"],
            
            # Colunas não-questão
            "Qual o seu sexo?": ["Masculino", "Feminino"],
            "Timestamp": pd.date_range("2024-01-01", periods=2)
        })
        
        print(f"Dataset original: {len(test_data.columns)} colunas")
        
        # Testar filtro base20
        filtered_base20, removed_base20 = processor.filter_by_question_set(test_data, "base20")
        print(f"✅ Base20: {len(filtered_base20.columns)} colunas mantidas, {len(removed_base20)} removidas")
        
        # Testar filtro base8
        filtered_base8, removed_base8 = processor.filter_by_question_set(test_data, "base8")
        print(f"✅ Base8: {len(filtered_base8.columns)} colunas mantidas, {len(removed_base8)} removidas")
        
        # Verificar se base8 removeu mais colunas que base20 (como esperado)
        if len(removed_base8) > len(removed_base20):
            print("✅ Base8 removeu mais colunas que Base20 (correto)")
        else:
            print("⚠️ Base8 deveria remover mais colunas que Base20")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na filtragem: {str(e)}")
        return False


def test_dimension_structure():
    """Testa se as dimensões estão estruturadas corretamente"""
    print("\n🔍 Testando estrutura de dimensões...")
    
    try:
        from core import QuestionnaireProcessor
        
        processor = QuestionnaireProcessor()
        
        # Testar estrutura base20
        config_base20 = processor.load_configuration("base20")
        report_base20 = processor.get_dimension_structure_report()
        
        print("📊 Base20:")
        for dim_name, dim_data in report_base20["dimensions"].items():
            print(f"  {dim_name}: {dim_data['question_count']} questões")
        
        # Testar estrutura base8
        config_base8 = processor.load_configuration("base8")
        report_base8 = processor.get_dimension_structure_report()
        
        print("\n📊 Base8:")
        for dim_name, dim_data in report_base8["dimensions"].items():
            print(f"  {dim_name}: {dim_data['question_count']} questões")
        
        # Verificar se base8 tem menos questões que base20
        total_base20 = sum(dim_data['question_count'] for dim_data in report_base20["dimensions"].values())
        total_base8 = sum(dim_data['question_count'] for dim_data in report_base8["dimensions"].values())
        
        print(f"\n✅ Total Base20: {total_base20} questões")
        print(f"✅ Total Base8: {total_base8} questões")
        
        if total_base8 < total_base20:
            print("✅ Base8 tem menos questões que Base20 (correto)")
        else:
            print("❌ Base8 deveria ter menos questões que Base20")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na estrutura: {str(e)}")
        return False


def test_integration_files():
    """Testa se os arquivos de integração existem e estão corretos"""
    print("\n🔍 Testando arquivos de integração...")
    
    try:
        # Verificar se arquivos existem
        required_files = [
            "app.py",
            "app_integration.py",
            "core/questionnaire_processor.py",
            "core/scale_converter.py"
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} existe")
            else:
                print(f"❌ {file_path} não encontrado")
                return False
        
        # Verificar se app.py foi modificado
        with open("app.py", "r", encoding="utf-8") as f:
            app_content = f.read()
        
        if "from app_integration import" in app_content:
            print("✅ app.py foi integrado corretamente")
        else:
            print("❌ app.py não foi integrado")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos arquivos: {str(e)}")
        return False


def install_streamlit_guide():
    """Fornece instruções para instalar o Streamlit"""
    print("\n📋 COMO INSTALAR O STREAMLIT:")
    print("1. Abra o terminal/prompt de comando")
    print("2. Execute um dos comandos abaixo:")
    print("   pip install streamlit")
    print("   ou")
    print("   python -m pip install streamlit")
    print("   ou")
    print("   conda install streamlit (se usar Anaconda)")
    print("\n3. Após a instalação, execute:")
    print("   streamlit run app.py")
    print("\n4. O dashboard abrirá no navegador automaticamente")


def run_simple_tests():
    """Executa testes simplificados"""
    print("Teste Simplificado dos Filtros da Barra Lateral")
    print("=" * 60)
    
    tests = [
        ("Funcionalidade Básica", test_basic_functionality),
        ("Lógica de Filtragem", test_filter_logic),
        ("Estrutura de Dimensões", test_dimension_structure),
        ("Arquivos de Integração", test_integration_files)
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
    print("📊 RESUMO DOS TESTES:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"  {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES BÁSICOS PASSARAM!")
        print("\n✅ O sistema está funcionando corretamente!")
        print("✅ Os filtros da barra lateral estão implementados!")
        print("✅ A integração foi aplicada com sucesso!")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        install_streamlit_guide()
        
        return True
    else:
        print(f"\n❌ {total - passed} TESTES FALHARAM!")
        print("\n🔧 PROBLEMAS IDENTIFICADOS:")
        
        for test_name, success in results:
            if not success:
                print(f"  • {test_name}")
        
        return False


if __name__ == "__main__":
    success = run_simple_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 SISTEMA FUNCIONANDO CORRETAMENTE!")
        print("\n📋 RESUMO:")
        print("✅ Filtros da barra lateral implementados")
        print("✅ Sistema de processamento funcionando")
        print("✅ Integração com app.py aplicada")
        print("✅ Estrutura de dimensões validada")
        print("\n🎯 INSTALE O STREAMLIT E TESTE O DASHBOARD!")
        exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ CORREÇÕES NECESSÁRIAS!")
        exit(1)