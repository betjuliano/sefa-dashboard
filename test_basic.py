"""
Teste basico sem emojis para compatibilidade com Windows
"""

import pandas as pd
import sys
import os

# Adicionar o diretório atual ao path para imports
sys.path.append('.')

def test_basic():
    """Teste basico do sistema"""
    print("Testando sistema basico...")
    
    try:
        from core import QuestionnaireProcessor, ScaleConverter
        
        # Testar carregamento
        processor = QuestionnaireProcessor()
        config = processor.load_configuration("base20")
        print("OK: Configuracao carregada")
        
        # Testar conversao
        converter = ScaleConverter()
        test_data = pd.Series(["Concordo", "Discordo"])
        result = converter.convert_likert_column(test_data)
        print("OK: Conversao funcionando")
        
        # Testar processamento
        df = pd.DataFrame({
            "O sistema e facil de usar.": ["Concordo", "Concordo"],
            "Sexo": ["M", "F"]
        })
        results = processor.process_questionnaire_data(df, "base20")
        print("OK: Processamento funcionando")
        
        return True
        
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    if test_basic():
        print("SUCESSO: Todos os testes passaram")
        exit(0)
    else:
        print("FALHA: Testes falharam")
        exit(1)