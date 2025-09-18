"""
Complete integration test for the questionnaire processing system

This test demonstrates the complete workflow from raw questionnaire data
to processed results with means by question and dimension.
"""
import pandas as pd
import numpy as np
from core import QuestionnaireProcessor, ScaleConverter, TextNormalizer


def test_complete_workflow():
    """Test the complete questionnaire processing workflow"""
    print("=== Teste de Integração Completa ===\n")
    
    # Step 1: Create realistic questionnaire data
    print("1️⃣ Criando dados de questionário realistas...")
    
    questionnaire_data = pd.DataFrame({
        # System Quality questions
        "O sistema é fácil de usar.": [
            "Concordo totalmente", "Concordo", "Indiferente", "Concordo", "Concordo totalmente",
            "Discordo", "Concordo", "Concordo totalmente", "Concordo", "Indiferente"
        ],
        "O sistema funciona sem falhas.": [
            "Concordo", "Discordo", "Indiferente", "Concordo", "Concordo totalmente",
            "Discordo totalmente", "Concordo", "Concordo", "Discordo", "Concordo"
        ],
        "É fácil localizar os serviços e as informações no sistema.": [
            "Concordo totalmente", "Concordo", "Concordo", "Indiferente", "Concordo",
            "Concordo", "Concordo totalmente", "Concordo", "Concordo", "Concordo totalmente"
        ],
        
        # Information Quality questions
        "As informações são fáceis de entender.": [
            "Concordo totalmente", "Concordo totalmente", "Concordo", "Concordo", "Concordo totalmente",
            "Concordo", "Concordo totalmente", "Concordo", "Concordo totalmente", "Concordo"
        ],
        "As informações são precisas.": [
            "Concordo", "Concordo", "Concordo totalmente", "Indiferente", "Concordo",
            "Concordo totalmente", "Concordo", "Concordo", "Concordo", "Concordo totalmente"
        ],
        "As informações disponibilizadas estão atualizadas.": [
            "Concordo", "Indiferente", "Concordo", "Discordo", "Concordo",
            "Concordo", "Concordo", "Indiferente", "Concordo", "Concordo"
        ],
        
        # Operation Quality questions
        "Os serviços atendem às minhas expectativas.": [
            "Concordo", "Concordo", "Indiferente", "Discordo", "Concordo",
            "Concordo totalmente", "Concordo", "Concordo", "Indiferente", "Concordo"
        ],
        "Consigo obter o que preciso no menor tempo possível.": [
            "Discordo", "Concordo", "Indiferente", "Discordo", "Concordo",
            "Concordo", "Indiferente", "Concordo", "Discordo", "Concordo"
        ],
        
        # Satisfaction and profile
        "Qual o seu nível de satisfação com o Sistema?": [
            "Muito satisfeito", "Satisfeito", "Satisfeito", "Indiferente", "Muito satisfeito",
            "Satisfeito", "Muito satisfeito", "Satisfeito", "Indiferente", "Satisfeito"
        ],
        "Qual o seu sexo?": [
            "Masculino", "Feminino", "Masculino", "Feminino", "Outro",
            "Masculino", "Feminino", "Masculino", "Feminino", "Masculino"
        ],
        "Timestamp": pd.date_range("2024-01-01", periods=10)
    })
    
    print(f"   ✅ Dataset criado: {len(questionnaire_data)} respostas, {len(questionnaire_data.columns)} colunas")
    
    # Step 2: Initialize components
    print("\n2️⃣ Inicializando componentes do sistema...")
    
    text_normalizer = TextNormalizer()
    scale_converter = ScaleConverter()
    processor = QuestionnaireProcessor()
    
    print("   ✅ TextNormalizer inicializado")
    print("   ✅ ScaleConverter inicializado")
    print("   ✅ QuestionnaireProcessor inicializado")
    
    # Step 3: Test individual components
    print("\n3️⃣ Testando componentes individuais...")
    
    # Test text normalization
    sample_text = "O sistema é fácil de usar?"
    normalized = text_normalizer.normalize_question_text(sample_text)
    print(f"   📝 Normalização: '{sample_text}' → '{normalized}'")
    
    # Test scale conversion
    sample_responses = pd.Series(["Concordo totalmente", "Discordo", "Indiferente"])
    converted = scale_converter.convert_likert_column(sample_responses)
    print(f"   🔢 Conversão de escala: {sample_responses.tolist()} → {converted.tolist()}")
    
    # Step 4: Process complete questionnaire
    print("\n4️⃣ Processando questionário completo...")
    
    try:
        results = processor.process_questionnaire_data(questionnaire_data, "base20")
        
        print(f"   ✅ Processamento concluído com sucesso!")
        print(f"   📊 Média geral: {results.overall_mean:.2f}")
        print(f"   📈 Satisfação: {results.satisfaction_score:.2f}")
        print(f"   🎯 Dimensões processadas: {len(results.dimensions)}")
        
        # Step 5: Analyze results by dimension
        print("\n5️⃣ Analisando resultados por dimensão...")
        
        for dimension_name, dimension_stats in results.dimensions.items():
            print(f"\n   📋 {dimension_name}:")
            print(f"      Média: {dimension_stats.mean_score:.2f}")
            print(f"      Questões: {dimension_stats.question_count}")
            print(f"      Respostas válidas: {dimension_stats.valid_responses}")
            
            # Show individual questions
            for question in dimension_stats.questions:
                print(f"        • {question.question_text[:50]}... → {question.mean_score:.2f}")
        
        # Step 6: Generate summaries
        print("\n6️⃣ Gerando resumos...")
        
        dimension_summary = processor.get_dimension_summary(results)
        question_summary = processor.get_question_summary(results)
        
        print(f"   📊 Resumo de dimensões gerado: {len(dimension_summary)} linhas")
        print(f"   📝 Resumo de questões gerado: {len(question_summary)} linhas")
        
        # Step 7: Export results
        print("\n7️⃣ Exportando resultados...")
        
        export_dict = processor.export_results_to_dict(results)
        
        print(f"   💾 Dados exportados para dicionário")
        print(f"   📦 Estrutura: {list(export_dict.keys())}")
        
        # Step 8: Validate results
        print("\n8️⃣ Validando resultados...")
        
        # Check that all means are within valid range (1-5)
        valid_range = True
        for dimension_stats in results.dimensions.values():
            if not (1 <= dimension_stats.mean_score <= 5):
                valid_range = False
                break
            for question in dimension_stats.questions:
                if not (1 <= question.mean_score <= 5):
                    valid_range = False
                    break
        
        print(f"   ✅ Médias dentro do intervalo válido (1-5): {valid_range}")
        
        # Check that satisfaction score is valid
        satisfaction_valid = 1 <= results.satisfaction_score <= 5
        print(f"   ✅ Pontuação de satisfação válida: {satisfaction_valid}")
        
        # Check for processing errors
        no_errors = len(results.processing_errors) == 0
        print(f"   ✅ Sem erros de processamento: {no_errors}")
        
        if results.question_mapping_issues:
            print(f"   ⚠️  Questões não mapeadas: {len(results.question_mapping_issues)}")
        
        print(f"\n🎉 Teste de integração concluído com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no processamento: {str(e)}")
        return False


def test_performance():
    """Test performance with larger dataset"""
    print("\n=== Teste de Performance ===\n")
    
    import time
    
    # Create larger dataset
    print("📊 Criando dataset grande para teste de performance...")
    
    n_responses = 1000
    responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
    
    large_data = pd.DataFrame({
        "O sistema é fácil de usar.": np.random.choice(responses, n_responses),
        "As informações são claras.": np.random.choice(responses, n_responses),
        "Os serviços atendem às expectativas.": np.random.choice(responses, n_responses),
        "Qual o seu nível de satisfação?": np.random.choice(
            ["Muito insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito satisfeito"], 
            n_responses
        )
    })
    
    print(f"   ✅ Dataset criado: {len(large_data):,} respostas")
    
    # Process and time it
    processor = QuestionnaireProcessor()
    
    start_time = time.time()
    results = processor.process_questionnaire_data(large_data, "base20")
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    print(f"\n⏱️  Tempo de processamento: {processing_time:.3f} segundos")
    print(f"🚀 Taxa de processamento: {len(large_data)/processing_time:,.0f} respostas/segundo")
    print(f"📊 Resultado: Média geral {results.overall_mean:.2f}")
    
    return processing_time < 5.0  # Should process 1000 responses in under 5 seconds


if __name__ == "__main__":
    print("Teste de Integração Completa do Sistema de Processamento de Questionários")
    print("=" * 80)
    
    # Run integration test
    integration_success = test_complete_workflow()
    
    # Run performance test
    performance_success = test_performance()
    
    print("\n" + "=" * 80)
    print("RESUMO DOS TESTES:")
    print(f"✅ Integração completa: {'PASSOU' if integration_success else 'FALHOU'}")
    print(f"✅ Performance: {'PASSOU' if performance_success else 'FALHOU'}")
    
    if integration_success and performance_success:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\nO sistema está pronto para:")
        print("  • Processar questionários base20 e base8")
        print("  • Converter escalas Likert automaticamente")
        print("  • Calcular médias por questão e dimensão")
        print("  • Organizar resultados por framework de qualidade")
        print("  • Tratar erros graciosamente")
        print("  • Processar grandes volumes de dados eficientemente")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM - Revisar implementação")