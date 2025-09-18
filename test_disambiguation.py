"""
Teste para demonstrar como o ScaleConverter distingue entre respostas similares
como "Discordo Totalmente" vs "Discordo" sem duplicação
"""
import pandas as pd
from core.scale_converter import ScaleConverter


def test_disambiguation():
    """Demonstra a distinção entre respostas similares"""
    print("=== Teste de Distinção entre Respostas Similares ===\n")
    
    converter = ScaleConverter()
    
    # Casos que podem ser confundidos
    test_cases = pd.Series([
        "Discordo totalmente",
        "Discordo",
        "Concordo totalmente", 
        "Concordo",
        "Eu discordo totalmente desta afirmação",
        "Eu discordo desta questão",
        "Concordo totalmente com isso",
        "Concordo com a proposta"
    ])
    
    print("Respostas de teste:")
    for i, response in enumerate(test_cases, 1):
        print(f"  {i}. '{response}'")
    
    # Converter
    results = converter.convert_likert_column(test_cases)
    
    print("\nResultados da conversão:")
    for i, (original, numeric) in enumerate(zip(test_cases, results), 1):
        print(f"  {i}. '{original}' → {numeric}")
    
    print("\nAnálise da lógica de matching:")
    
    # Mostrar como funciona internamente
    for i, response in enumerate(test_cases):
        print(f"\n{i+1}. Processando: '{response}'")
        
        # Normalizar o texto
        from core.text_normalizer import TextNormalizer
        normalized = TextNormalizer.normalize_response_text(response)
        print(f"   Normalizado: '{normalized}'")
        
        # Verificar matches exatos primeiro
        exact_matches = []
        for key in converter.expanded_mapping.keys():
            if key == normalized:
                exact_matches.append(key)
        
        if exact_matches:
            print(f"   Match exato encontrado: {exact_matches}")
        else:
            # Verificar matches parciais
            partial_matches = []
            for key in converter.expanded_mapping.keys():
                if len(key) > 3 and key in normalized:
                    partial_matches.append((key, len(key)))
            
            if partial_matches:
                # Ordenar por comprimento (mais específico primeiro)
                partial_matches.sort(key=lambda x: x[1], reverse=True)
                print(f"   Matches parciais (ordenados por especificidade): {partial_matches}")
                best_match = partial_matches[0][0]
                print(f"   Melhor match: '{best_match}' (comprimento: {partial_matches[0][1]})")
            else:
                print("   Nenhum match encontrado")
        
        print(f"   Resultado final: {results.iloc[i]}")


def test_priority_order():
    """Testa a ordem de prioridade no matching"""
    print("\n\n=== Teste de Ordem de Prioridade ===\n")
    
    converter = ScaleConverter()
    
    # Casos onde uma resposta contém múltiplas palavras-chave
    ambiguous_cases = pd.Series([
        "Discordo totalmente, não concordo",
        "Concordo, mas não totalmente",
        "Totalmente em desacordo"
    ])
    
    print("Casos ambíguos:")
    for i, response in enumerate(ambiguous_cases, 1):
        print(f"  {i}. '{response}'")
    
    results = converter.convert_likert_column(ambiguous_cases)
    
    print("\nResultados (prioriza match mais longo/específico):")
    for i, (original, numeric) in enumerate(zip(ambiguous_cases, results), 1):
        print(f"  {i}. '{original}' → {numeric}")


def test_edge_cases():
    """Testa casos extremos de similaridade"""
    print("\n\n=== Teste de Casos Extremos ===\n")
    
    converter = ScaleConverter()
    
    edge_cases = pd.Series([
        "Discordo",
        "Discordo muito",
        "Discordo totalmente",
        "Discordo completamente",
        "Concordo",
        "Concordo muito", 
        "Concordo totalmente",
        "Concordo completamente"
    ])
    
    print("Casos extremos:")
    for i, response in enumerate(edge_cases, 1):
        print(f"  {i}. '{response}'")
    
    results = converter.convert_likert_column(edge_cases)
    
    print("\nResultados:")
    for i, (original, numeric) in enumerate(zip(edge_cases, results), 1):
        expected = ""
        if "totalmente" in original.lower() or "completamente" in original.lower():
            if "concordo" in original.lower():
                expected = " (esperado: 5 - Concordo Totalmente)"
            elif "discordo" in original.lower():
                expected = " (esperado: 1 - Discordo Totalmente)"
        elif "concordo" in original.lower():
            expected = " (esperado: 4 - Concordo)"
        elif "discordo" in original.lower():
            expected = " (esperado: 2 - Discordo)"
            
        print(f"  {i}. '{original}' → {numeric}{expected}")


if __name__ == "__main__":
    test_disambiguation()
    test_priority_order()
    test_edge_cases()