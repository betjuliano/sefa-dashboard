"""
Demonstration of sidebar filter functionality

This script shows how the QuestionnaireProcessor handles different question sets
and simulates the sidebar filter behavior for switching between question sets.
"""
import pandas as pd
import numpy as np
from core.questionnaire_processor import QuestionnaireProcessor


def create_comprehensive_dataset():
    """Create a comprehensive dataset with questions from both base20 and base8"""
    np.random.seed(42)
    
    responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
    satisfaction_responses = ["Muito insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito satisfeito"]
    
    n_responses = 50
    
    # Create dataset with questions from both configurations
    data = {}
    
    # Base20 questions (Sistema)
    base20_qs_questions = [
        "O sistema funciona sem falhas.",
        "Os recursos de acessibilidade do sistema são fáceis de encontrar.",
        "O sistema é fácil de usar.",
        "O sistema está disponível para uso em qualquer dia e hora.",
        "O desempenho do sistema é satisfatório, independentemente da forma de acesso.",
        "O sistema informa sobre as políticas de privacidade e segurança.",
        "Acredito que meus dados estão seguros neste sistema.",
        "É fácil localizar os serviços e as informações no sistema.",
        "A navegação pelo sistema é intuitiva.",
        "O sistema oferece instruções úteis de como utilizar os serviços."
    ]
    
    # Base8 questions (Portal) - some overlap with base20
    base8_qs_questions = [
        "O Portal é fácil de usar.",
        "É fácil localizar os dados e as informações no Portal.",
        "A navegação pelo Portal é intuitiva.",
        "O Portal funciona sem falhas."
    ]
    
    # Information Quality questions (common structure)
    qi_questions = [
        "As informações são fáceis de entender.",
        "As informações são precisas.",
        "As informações disponibilizadas estão atualizadas.",
        "As informações auxiliam na solicitação dos serviços.",
        "Todas as informações necessárias para a solicitação dos serviços são fornecidas.",
        "O prazo de entrega dos serviços é informado.",
        "As taxas cobradas pelos serviços são informadas."
    ]
    
    # Operation Quality questions
    qo_questions = [
        "Os serviços oferecem suporte técnico eficiente.",
        "O atendimento resolve meus problemas.",
        "Os serviços permitem a conclusão das tarefas no menor tempo possível.",
        "Consigo obter o que preciso no menor tempo possível.",
        "Os serviços atendem às minhas expectativas.",
        "Quando preciso de ajuda, minhas dificuldades são resolvidas.",
        "Meus dados são automaticamente identificados na solicitação dos serviços.",
        "Os serviços oferecidos são confiáveis.",
        "Os serviços permitem interações em tempo real (ex. chatbot, IA)."
    ]
    
    # Generate responses for all questions
    all_questions = base20_qs_questions + base8_qs_questions + qi_questions + qo_questions
    
    for question in all_questions:
        # Vary response patterns slightly
        weights = np.random.dirichlet([1, 2, 3, 4, 3])  # Slightly positive bias
        data[question] = np.random.choice(responses, n_responses, p=weights)
    
    # Add satisfaction and profile data
    data["Qual o seu nível de satisfação com o Sistema?"] = np.random.choice(satisfaction_responses, n_responses)
    data["Qual o seu nível de satisfação com o Portal da Transparência do RS?"] = np.random.choice(satisfaction_responses, n_responses)
    data["Qual o seu sexo?"] = np.random.choice(["Masculino", "Feminino", "Outro"], n_responses, p=[0.45, 0.50, 0.05])
    data["Qual a sua idade?"] = np.random.choice(["18-25", "26-35", "36-45", "46-55", "56+"], n_responses)
    data["Timestamp"] = pd.date_range("2024-01-01", periods=n_responses)
    
    return pd.DataFrame(data)


def demo_sidebar_filter_options():
    """Demonstrate available sidebar filter options"""
    print("=== Opções de Filtro da Barra Lateral ===\n")
    
    processor = QuestionnaireProcessor()
    filter_options = processor.get_sidebar_filter_options()
    
    for filter_name, details in filter_options.items():
        status = "✅ Disponível" if details["available"] else "❌ Não disponível"
        print(f"📋 {filter_name} ({status})")
        print(f"   Descrição: {details['description']}")
        print(f"   Total de questões: {details['total_questions']}")
        print(f"   Dimensões:")
        for dim, count in details["dimensions"].items():
            print(f"     {dim}: {count} questões")
        if details.get("note"):
            print(f"   ⚠️  {details['note']}")
        print()


def demo_dimension_structure_validation():
    """Demonstrate dimension structure validation"""
    print("=== Validação da Estrutura de Dimensões ===\n")
    
    processor = QuestionnaireProcessor()
    
    # Test both configurations
    for question_set in ["base20", "base8"]:
        print(f"🔍 Carregando configuração {question_set}...")
        try:
            config = processor.load_configuration(question_set)
            
            # Get structure report
            report = processor.get_dimension_structure_report()
            
            print(f"\n📊 Relatório de Estrutura - {question_set.upper()}:")
            print(f"   Total de questões: {report['total_questions']}")
            
            for dim_name, dim_data in report["dimensions"].items():
                print(f"   {dim_name}: {dim_data['question_count']} questões")
            
            # Show validation results
            if "validation" in report and report["validation"]:
                print(f"\n✅ Validação:")
                for dim_name, validation in report["validation"].items():
                    status = "✅" if validation["valid"] else "⚠️"
                    print(f"   {status} {dim_name}: {validation['actual']} questões (esperado: {validation['expected']})")
                    if not validation["valid"]:
                        print(f"      Diferença: {validation['difference']:+d}")
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
        
        print("-" * 50)


def demo_question_set_filtering():
    """Demonstrate filtering data by question set"""
    print("\n=== Filtragem por Conjunto de Questões ===\n")
    
    # Create comprehensive dataset
    df = create_comprehensive_dataset()
    print(f"📊 Dataset original criado: {len(df)} respostas, {len(df.columns)} colunas")
    
    processor = QuestionnaireProcessor()
    
    # Test filtering for each question set
    for question_set in ["base20", "base8"]:
        print(f"\n🔽 Filtrando para {question_set}...")
        
        try:
            filtered_df, removed_cols = processor.filter_by_question_set(df, question_set)
            
            print(f"   ✅ Filtro aplicado:")
            print(f"      Colunas mantidas: {len(filtered_df.columns)}")
            print(f"      Colunas removidas: {len(removed_cols)}")
            
            if removed_cols:
                print(f"      Primeiras colunas removidas:")
                for col in removed_cols[:3]:
                    print(f"        - {col}")
                if len(removed_cols) > 3:
                    print(f"        ... e mais {len(removed_cols) - 3}")
            
        except Exception as e:
            print(f"   ❌ Erro no filtro: {str(e)}")


def demo_comparative_analysis():
    """Demonstrate comparative analysis between question sets"""
    print("\n=== Análise Comparativa entre Conjuntos ===\n")
    
    # Create dataset
    df = create_comprehensive_dataset()
    
    processor = QuestionnaireProcessor()
    
    print("🔍 Executando análise comparativa...")
    comparison = processor.compare_question_sets(df)
    
    print(f"\n📊 Dados Originais:")
    print(f"   Total de colunas: {comparison['original_data']['total_columns']}")
    print(f"   Total de linhas: {comparison['original_data']['total_rows']}")
    
    print(f"\n📈 Comparação entre Conjuntos de Questões:")
    
    for question_set, results in comparison["question_sets"].items():
        if "error" in results:
            print(f"\n❌ {question_set.upper()}: {results['error']}")
            continue
        
        print(f"\n✅ {question_set.upper()}:")
        print(f"   Colunas após filtro: {results['filtered_columns']}")
        print(f"   Colunas removidas: {results['removed_columns']}")
        print(f"   Média geral: {results['overall_mean']:.2f}")
        print(f"   Satisfação: {results['satisfaction_score']:.2f}" if results['satisfaction_score'] else "   Satisfação: N/A")
        
        print(f"   Dimensões:")
        for dim_name, dim_stats in results["dimensions"].items():
            print(f"     {dim_name}: {dim_stats['mean_score']:.2f} ({dim_stats['question_count']} questões)")
        
        # Show validation status
        if results.get("structure_validation"):
            validation_issues = sum(1 for v in results["structure_validation"].values() if not v.get("valid", True))
            if validation_issues == 0:
                print(f"   ✅ Estrutura validada corretamente")
            else:
                print(f"   ⚠️  {validation_issues} problemas de estrutura detectados")
        
        if results.get("processing_errors", 0) > 0:
            print(f"   ⚠️  {results['processing_errors']} erros de processamento")
        
        if results.get("mapping_issues", 0) > 0:
            print(f"   🔍 {results['mapping_issues']} questões não mapeadas")


def demo_real_world_scenario():
    """Demonstrate a real-world scenario of switching filters"""
    print("\n=== Cenário Real: Mudança de Filtros ===\n")
    
    # Simulate user uploading data and switching filters
    df = create_comprehensive_dataset()
    processor = QuestionnaireProcessor()
    
    print("👤 Usuário carrega arquivo com dados de questionário...")
    print(f"   📁 Arquivo carregado: {len(df)} respostas, {len(df.columns)} colunas")
    
    # Simulate sidebar filter changes
    filter_sequence = [
        ("base20", "20 questões"),
        ("base8", "8 questões"),
        ("base20", "20 questões")  # Switch back
    ]
    
    results_cache = {}
    
    for question_set, filter_name in filter_sequence:
        print(f"\n🔄 Usuário seleciona filtro: '{filter_name}'")
        
        # Check if we already processed this
        if question_set in results_cache:
            print(f"   ⚡ Usando resultado em cache...")
            results = results_cache[question_set]
        else:
            print(f"   🔄 Processando dados para {question_set}...")
            
            # Filter and process
            filtered_df, removed_cols = processor.filter_by_question_set(df, question_set)
            results = processor.process_questionnaire_data(filtered_df, question_set)
            results_cache[question_set] = results
            
            print(f"   ✅ Processamento concluído")
        
        # Show results as they would appear in the dashboard
        print(f"\n   📊 Dashboard atualizado:")
        print(f"      Média Geral: {results.overall_mean:.2f}")
        print(f"      Satisfação: {results.satisfaction_score:.2f}" if results.satisfaction_score else "      Satisfação: N/A")
        print(f"      Dimensões processadas: {len(results.dimensions)}")
        
        for dim_name, dim_stats in results.dimensions.items():
            print(f"        {dim_name}: {dim_stats.mean_score:.2f}")


if __name__ == "__main__":
    print("Demonstração dos Filtros da Barra Lateral")
    print("=" * 60)
    
    demo_sidebar_filter_options()
    demo_dimension_structure_validation()
    demo_question_set_filtering()
    demo_comparative_analysis()
    demo_real_world_scenario()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMO:")
    print("✅ Sistema suporta filtros da barra lateral")
    print("✅ Validação automática da estrutura de dimensões")
    print("✅ Filtragem dinâmica por conjunto de questões")
    print("✅ Análise comparativa entre conjuntos")
    print("✅ Cache de resultados para performance")
    print("✅ Relatórios detalhados de estrutura")
    
    print("\n📋 ESTRUTURA ATUAL:")
    print("Base20: QS(10), QI(7), QO(9) = 26 questões")
    print("Base8:  QS(4), QI(3), QO(1) = 8 questões")
    print("\n⚠️  NOTA: Base20 tem 26 questões (não 20) na configuração atual")