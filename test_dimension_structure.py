"""
Teste para verificar se o QuestionnaireProcessor está processando corretamente
a estrutura de dimensões do Base20 e Base8
"""
import pandas as pd
import numpy as np
from core.questionnaire_processor import QuestionnaireProcessor


def create_base20_sample_data():
    """Cria dados de amostra que correspondem à estrutura Base20"""
    
    # QS - 10 questões
    qs_questions = [
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
    
    # QI - 7 questões
    qi_questions = [
        "As informações são fáceis de entender.",
        "As informações são precisas.",
        "As informações auxiliam na solicitação dos serviços.",
        "Todas as informações necessárias para a solicitação dos serviços são fornecidas.",
        "O prazo de entrega dos serviços é informado.",
        "As taxas cobradas pelos serviços são informadas.",
        "As informações disponibilizadas estão atualizadas."
    ]
    
    # QO - 9 questões
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
    
    # Criar dados de amostra
    responses = ["Discordo totalmente", "Discordo", "Indiferente", "Concordo", "Concordo totalmente"]
    n_responses = 50
    
    data = {}
    
    # Adicionar todas as questões
    all_questions = qs_questions + qi_questions + qo_questions
    for question in all_questions:
        data[question] = np.random.choice(responses, n_responses)
    
    # Adicionar satisfação
    data["Qual o seu nível de satisfação com o Sistema?"] = np.random.choice(
        ["Muito insatisfeito", "Insatisfeito", "Indiferente", "Satisfeito", "Muito satisfeito"], 
        n_responses
    )
    
    return pd.DataFrame(data)


def create_base8_sample_data():
    """Cria dados de amostra que correspondem à estrutura Base8"""
    
    # QS - 4 questões
    qs_questions = [
        "O Portal é fácil de usar.",
        "É fácil localizar os dados e as informações no Portal.",
        "A navegação pelo Portal é intuitiva.",
        "O Portal funciona sem falhas."
    ]
    
    # QI - 3 questões
    qi_questions = [
        "As informações são fáceis de entender.",
        "As informações são precisas.",
        "As informações disponibilizadas estão atualizadas."
    ]
    
    # QO - 1 questão
    qo_questions = [
        "Consigo obter o que preciso no menor tempo possível."
    ]
    
    # Criar dados de amostra
    responses = ["Discordo totalmente", "Discordo", "Neutro", "Concordo", "Concordo totalmente"]
    n_responses = 30
    
    data = {}
    
    # Adicionar todas as questões
    all_questions = qs_questions + qi_questions + qo_questions
    for question in all_questions:
        data[question] = np.random.choice(responses, n_responses)
    
    # Adicionar satisfação
    data["Qual o seu nível de satisfação com o Portal da Transparência do RS?"] = np.random.choice(
        ["Muito insatisfeito", "Insatisfeito", "Neutro", "Satisfeito", "Muito satisfeito"], 
        n_responses
    )
    
    return pd.DataFrame(data)


def test_base20_structure():
    """Testa o processamento da estrutura Base20"""
    print("=== Teste Base20 ===\n")
    
    # Criar dados de amostra
    df = create_base20_sample_data()
    print(f"📊 Dataset Base20 criado: {len(df)} respostas, {len(df.columns)} colunas")
    
    # Processar
    processor = QuestionnaireProcessor()
    results = processor.process_questionnaire_data(df, "base20")
    
    print(f"\n📋 Resultados Base20:")
    print(f"  Média Geral: {results.overall_mean:.2f}")
    print(f"  Dimensões Processadas: {len(results.dimensions)}")
    
    # Verificar estrutura das dimensões
    expected_structure = {
        "Qualidade do Sistema": 10,
        "Qualidade da Informação": 7,
        "Qualidade da Operação": 9
    }
    
    print(f"\n🎯 Verificação da Estrutura:")
    all_correct = True
    
    for dimension_name, expected_count in expected_structure.items():
        if dimension_name in results.dimensions:
            actual_count = results.dimensions[dimension_name].question_count
            status = "✅" if actual_count == expected_count else "❌"
            print(f"  {status} {dimension_name}: {actual_count}/{expected_count} questões")
            if actual_count != expected_count:
                all_correct = False
        else:
            print(f"  ❌ {dimension_name}: DIMENSÃO NÃO ENCONTRADA")
            all_correct = False
    
    if results.processing_errors:
        print(f"\n⚠️  Erros: {len(results.processing_errors)}")
        for error in results.processing_errors[:3]:
            print(f"    - {error}")
    
    if results.question_mapping_issues:
        print(f"\n🔍 Questões não mapeadas: {len(results.question_mapping_issues)}")
    
    return all_correct


def test_base8_structure():
    """Testa o processamento da estrutura Base8"""
    print("\n=== Teste Base8 ===\n")
    
    # Criar dados de amostra
    df = create_base8_sample_data()
    print(f"📊 Dataset Base8 criado: {len(df)} respostas, {len(df.columns)} colunas")
    
    # Processar
    processor = QuestionnaireProcessor()
    results = processor.process_questionnaire_data(df, "base8")
    
    print(f"\n📋 Resultados Base8:")
    print(f"  Média Geral: {results.overall_mean:.2f}")
    print(f"  Dimensões Processadas: {len(results.dimensions)}")
    
    # Verificar estrutura das dimensões
    expected_structure = {
        "Qualidade do Sistema": 4,
        "Qualidade da Informação": 3,
        "Qualidade da Operação": 1
    }
    
    print(f"\n🎯 Verificação da Estrutura:")
    all_correct = True
    
    for dimension_name, expected_count in expected_structure.items():
        if dimension_name in results.dimensions:
            actual_count = results.dimensions[dimension_name].question_count
            status = "✅" if actual_count == expected_count else "❌"
            print(f"  {status} {dimension_name}: {actual_count}/{expected_count} questões")
            if actual_count != expected_count:
                all_correct = False
        else:
            print(f"  ❌ {dimension_name}: DIMENSÃO NÃO ENCONTRADA")
            all_correct = False
    
    if results.processing_errors:
        print(f"\n⚠️  Erros: {len(results.processing_errors)}")
        for error in results.processing_errors[:3]:
            print(f"    - {error}")
    
    if results.question_mapping_issues:
        print(f"\n🔍 Questões não mapeadas: {len(results.question_mapping_issues)}")
    
    return all_correct


def test_dimension_switching():
    """Testa a troca entre Base20 e Base8"""
    print("\n=== Teste de Troca de Dimensões ===\n")
    
    processor = QuestionnaireProcessor()
    
    # Testar carregamento de configurações
    print("🔄 Testando carregamento de configurações...")
    
    # Carregar Base20
    config_base20 = processor.load_configuration("base20")
    print(f"  ✅ Base20 carregado: {len(config_base20['dimensions'])} dimensões")
    
    # Carregar Base8
    config_base8 = processor.load_configuration("base8")
    print(f"  ✅ Base8 carregado: {len(config_base8['dimensions'])} dimensões")
    
    # Verificar que as configurações são diferentes
    base20_total = sum(len(questions) for questions in config_base20['dimensions'].values())
    base8_total = sum(len(questions) for questions in config_base8['dimensions'].values())
    
    print(f"\n📊 Total de questões:")
    print(f"  Base20: {base20_total} questões")
    print(f"  Base8: {base8_total} questões")
    
    return base20_total != base8_total


def main():
    """Executa todos os testes"""
    print("Teste de Estrutura das Dimensões")
    print("=" * 50)
    
    # Executar testes
    base20_ok = test_base20_structure()
    base8_ok = test_base8_structure()
    switching_ok = test_dimension_switching()
    
    # Resumo
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES:")
    print(f"✅ Base20 estrutura correta: {'SIM' if base20_ok else 'NÃO'}")
    print(f"✅ Base8 estrutura correta: {'SIM' if base8_ok else 'NÃO'}")
    print(f"✅ Troca de configurações: {'SIM' if switching_ok else 'NÃO'}")
    
    if base20_ok and base8_ok and switching_ok:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\nO sistema está processando corretamente:")
        print("  • Base20: QS=10, QI=7, QO=9 questões")
        print("  • Base8: QS=4, QI=3, QO=1 questão")
        print("  • Troca dinâmica entre configurações")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM")
        if not base20_ok:
            print("  - Base20 não está processando a estrutura correta")
        if not base8_ok:
            print("  - Base8 não está processando a estrutura correta")
        if not switching_ok:
            print("  - Troca de configurações não está funcionando")


if __name__ == "__main__":
    main()