"""
Demonstration script for QuestionnaireProcessor functionality

This script shows how to use the QuestionnaireProcessor class for processing
questionnaire data, calculating means by question and dimension, and organizing
results according to the quality framework.
"""
import pandas as pd
import numpy as np
from core.questionnaire_processor import QuestionnaireProcessor


def create_sample_data():
    """Create realistic sample questionnaire data"""
    np.random.seed(42)  # For reproducible results
    
    # Create responses with realistic distribution
    responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
    weights = [0.05, 0.15, 0.20, 0.35, 0.25]  # More positive responses
    
    n_responses = 100
    
    # Generate responses for each question
    data = {}
    
    # System Quality questions
    data["O sistema é fácil de usar."] = np.random.choice(responses, n_responses, p=weights)
    data["O sistema funciona sem falhas."] = np.random.choice(responses, n_responses, p=[0.08, 0.20, 0.25, 0.30, 0.17])
    data["É fácil localizar os serviços e as informações no sistema."] = np.random.choice(responses, n_responses, p=weights)
    data["A navegação pelo sistema é intuitiva."] = np.random.choice(responses, n_responses, p=weights)
    
    # Information Quality questions  
    data["As informações são fáceis de entender."] = np.random.choice(responses, n_responses, p=[0.03, 0.12, 0.18, 0.40, 0.27])
    data["As informações são precisas."] = np.random.choice(responses, n_responses, p=[0.02, 0.08, 0.15, 0.45, 0.30])
    data["As informações disponibilizadas estão atualizadas."] = np.random.choice(responses, n_responses, p=[0.05, 0.15, 0.25, 0.35, 0.20])
    
    # Operation Quality questions
    data["Os serviços atendem às minhas expectativas."] = np.random.choice(responses, n_responses, p=[0.07, 0.18, 0.22, 0.33, 0.20])
    data["Consigo obter o que preciso no menor tempo possível."] = np.random.choice(responses, n_responses, p=[0.10, 0.20, 0.25, 0.30, 0.15])
    
    # Satisfaction question
    satisfaction_responses = ["Muito insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito satisfeito"]
    data["Qual o seu nível de satisfação com o Sistema?"] = np.random.choice(satisfaction_responses, n_responses, p=[0.05, 0.15, 0.20, 0.40, 0.20])
    
    # Profile questions
    data["Qual o seu sexo?"] = np.random.choice(["Masculino", "Feminino", "Outro"], n_responses, p=[0.45, 0.50, 0.05])
    data["Qual a sua idade?"] = np.random.choice(["18-25", "26-35", "36-45", "46-55", "56+"], n_responses, p=[0.20, 0.25, 0.25, 0.20, 0.10])
    
    # Add some missing values to make it realistic
    for col in data:
        if "satisfação" not in col.lower() and "sexo" not in col.lower() and "idade" not in col.lower():
            # Add 5% missing values to question columns
            missing_indices = np.random.choice(n_responses, int(n_responses * 0.05), replace=False)
            for idx in missing_indices:
                data[col][idx] = ""
    
    return pd.DataFrame(data)


def demo_basic_processing():
    """Demonstrate basic questionnaire processing"""
    print("=== Demonstração Básica do QuestionnaireProcessor ===\n")
    
    # Create sample data
    df = create_sample_data()
    print(f"Dataset criado com {len(df)} respostas e {len(df.columns)} colunas")
    print(f"Colunas: {list(df.columns)[:3]}... (e mais {len(df.columns)-3})")
    
    # Initialize processor
    processor = QuestionnaireProcessor()
    
    try:
        # Process the data
        results = processor.process_questionnaire_data(df, "base20")
        
        print(f"\n📊 Resultados Gerais:")
        print(f"  Média Geral: {results.overall_mean:.2f}")
        print(f"  Total de Respostas: {results.total_responses}")
        print(f"  Respostas Válidas: {results.valid_responses}")
        print(f"  Satisfação Geral: {results.satisfaction_score:.2f}" if results.satisfaction_score else "  Satisfação: Não disponível")
        
        print(f"\n🎯 Dimensões Processadas: {len(results.dimensions)}")
        for dimension_name, dimension_stats in results.dimensions.items():
            print(f"  {dimension_name}: {dimension_stats.mean_score:.2f} ({dimension_stats.question_count} questões)")
        
        if results.processing_errors:
            print(f"\n⚠️  Erros de Processamento: {len(results.processing_errors)}")
            for error in results.processing_errors[:3]:
                print(f"  - {error}")
        
        if results.question_mapping_issues:
            print(f"\n🔍 Questões Não Mapeadas: {len(results.question_mapping_issues)}")
            for issue in results.question_mapping_issues[:3]:
                print(f"  - {issue}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        return None


def demo_detailed_analysis(results):
    """Demonstrate detailed analysis capabilities"""
    if not results:
        return
    
    print("\n=== Análise Detalhada por Dimensão ===\n")
    
    processor = QuestionnaireProcessor()
    
    # Get dimension summary
    dimension_summary = processor.get_dimension_summary(results)
    print("📋 Resumo por Dimensão:")
    print(dimension_summary.to_string(index=False))
    
    # Get question summary
    question_summary = processor.get_question_summary(results)
    print(f"\n📝 Resumo Detalhado por Questão (primeiras 5):")
    print(question_summary.head().to_string(index=False))
    
    # Show best and worst performing questions
    question_summary_sorted = question_summary.sort_values('Média', ascending=False)
    
    print(f"\n🏆 Top 3 Questões com Melhor Avaliação:")
    top_questions = question_summary_sorted.head(3)
    for _, row in top_questions.iterrows():
        print(f"  {row['Média']:.2f} - {row['Questão'][:60]}...")
    
    print(f"\n📉 Top 3 Questões com Pior Avaliação:")
    bottom_questions = question_summary_sorted.tail(3)
    for _, row in bottom_questions.iterrows():
        print(f"  {row['Média']:.2f} - {row['Questão'][:60]}...")


def demo_export_capabilities(results):
    """Demonstrate export capabilities"""
    if not results:
        return
    
    print("\n=== Capacidades de Exportação ===\n")
    
    processor = QuestionnaireProcessor()
    
    # Export to dictionary
    export_dict = processor.export_results_to_dict(results)
    
    print("📤 Dados Exportados para Dicionário:")
    print(f"  Estatísticas Gerais: {len(export_dict['overall_statistics'])} campos")
    print(f"  Dimensões: {len(export_dict['dimensions'])} dimensões")
    print(f"  Informações de Processamento: {len(export_dict['processing_info'])} campos")
    
    # Show sample of exported data
    print(f"\n📊 Amostra dos Dados Exportados:")
    overall_stats = export_dict['overall_statistics']
    for key, value in overall_stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Show dimension details
    print(f"\n🎯 Detalhes das Dimensões:")
    for dim_name, dim_data in export_dict['dimensions'].items():
        print(f"  {dim_name}:")
        print(f"    Média: {dim_data['mean_score']:.2f}")
        print(f"    Questões: {dim_data['question_count']}")
        print(f"    Respostas Válidas: {dim_data['valid_responses']}")


def demo_comparison_base20_vs_base8():
    """Demonstrate comparison between base20 and base8 processing"""
    print("\n=== Comparação Base20 vs Base8 ===\n")
    
    # Create smaller dataset that works for both
    common_questions_data = pd.DataFrame({
        "O sistema é fácil de usar.": ["Concordo totalmente", "Concordo", "Indiferente", "Concordo", "Concordo totalmente"],
        "As informações são claras.": ["Concordo", "Concordo totalmente", "Concordo", "Indiferente", "Concordo"],
        "Consigo obter o que preciso no menor tempo possível.": ["Concordo", "Concordo", "Concordo totalmente", "Concordo", "Indiferente"],
        "Qual o seu nível de satisfação?": ["Muito satisfeito", "Satisfeito", "Satisfeito", "Indiferente", "Muito satisfeito"]
    })
    
    processor = QuestionnaireProcessor()
    
    try:
        # Process with base20
        results_base20 = processor.process_questionnaire_data(common_questions_data, "base20")
        print("📊 Processamento Base20:")
        print(f"  Média Geral: {results_base20.overall_mean:.2f}")
        print(f"  Dimensões: {len(results_base20.dimensions)}")
        
        # Process with base8
        results_base8 = processor.process_questionnaire_data(common_questions_data, "base8")
        print(f"\n📊 Processamento Base8:")
        print(f"  Média Geral: {results_base8.overall_mean:.2f}")
        print(f"  Dimensões: {len(results_base8.dimensions)}")
        
        # Compare dimensions
        print(f"\n🔍 Comparação de Dimensões:")
        for dim_name in results_base20.dimensions:
            if dim_name in results_base8.dimensions:
                base20_mean = results_base20.dimensions[dim_name].mean_score
                base8_mean = results_base8.dimensions[dim_name].mean_score
                print(f"  {dim_name}:")
                print(f"    Base20: {base20_mean:.2f}")
                print(f"    Base8:  {base8_mean:.2f}")
                print(f"    Diferença: {abs(base20_mean - base8_mean):.2f}")
        
    except Exception as e:
        print(f"❌ Erro na comparação: {str(e)}")


def demo_error_handling():
    """Demonstrate error handling capabilities"""
    print("\n=== Demonstração de Tratamento de Erros ===\n")
    
    processor = QuestionnaireProcessor()
    
    # Test with problematic data
    problematic_data = pd.DataFrame({
        "Questão Inexistente 1": ["Concordo", "Discordo", "Indiferente"],
        "Questão Inexistente 2": ["Sim", "Não", "Talvez"],
        "Dados Numéricos": [1, 2, 3],
        "Dados Mistos": ["Concordo", 123, None]
    })
    
    try:
        results = processor.process_questionnaire_data(problematic_data, "base20")
        
        print("📊 Resultados com Dados Problemáticos:")
        print(f"  Média Geral: {results.overall_mean}")
        print(f"  Dimensões Processadas: {len(results.dimensions)}")
        print(f"  Erros de Processamento: {len(results.processing_errors)}")
        print(f"  Questões Não Mapeadas: {len(results.question_mapping_issues)}")
        
        if results.processing_errors:
            print(f"\n⚠️  Erros Encontrados:")
            for error in results.processing_errors:
                print(f"  - {error}")
        
        if results.question_mapping_issues:
            print(f"\n🔍 Questões Não Mapeadas:")
            for issue in results.question_mapping_issues:
                print(f"  - {issue}")
        
    except Exception as e:
        print(f"❌ Erro crítico: {str(e)}")


if __name__ == "__main__":
    print("Demonstração do QuestionnaireProcessor")
    print("=" * 60)
    
    # Run all demonstrations
    results = demo_basic_processing()
    demo_detailed_analysis(results)
    demo_export_capabilities(results)
    demo_comparison_base20_vs_base8()
    demo_error_handling()
    
    print("\n" + "=" * 60)
    print("Demonstração concluída!")
    print("\nO QuestionnaireProcessor oferece:")
    print("✅ Processamento automático de escalas Likert")
    print("✅ Cálculo de médias por questão e dimensão")
    print("✅ Organização por framework de qualidade (QS, QI, QO)")
    print("✅ Tratamento robusto de erros")
    print("✅ Suporte para base20 e base8")
    print("✅ Exportação flexível de resultados")
    print("✅ Validação e relatórios de qualidade de dados")