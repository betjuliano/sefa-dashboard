"""
Script simples para preparar deploy no Vercel
Sem emojis para compatibilidade com Windows
"""
import os
import json

def check_files():
    """Verifica arquivos necessarios"""
    print("Verificando arquivos necessarios...")
    
    required = [
        "app.py",
        "app_integration.py",
        "core/scale_converter.py", 
        "core/questionnaire_processor.py",
        "config/items_mapping.json",
        "config/items_mapping_8q.json",
        "vercel.json",
        "requirements.txt"
    ]
    
    missing = []
    for file in required:
        if os.path.exists(file):
            print(f"OK: {file}")
        else:
            print(f"FALTANDO: {file}")
            missing.append(file)
    
    return len(missing) == 0

def create_readme():
    """Cria README simples"""
    readme = """# Dashboard de Qualidade - Sistema de Questionarios

Sistema completo de processamento e analise de questionarios.

## Funcionalidades
- Filtros da barra lateral dinamicos
- Processamento robusto de escalas Likert
- Analise por dimensoes (QS, QI, QO)
- Validacao automatica de estrutura

## Estrutura de Dados
### Base20 (26 questoes)
- QS: 10 questoes
- QI: 7 questoes  
- QO: 9 questoes

### Base8 (8 questoes)
- QS: 4 questoes
- QI: 3 questoes
- QO: 1 questao

## Deploy
Configurado para deploy automatico no Vercel.
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("README.md criado")

def main():
    """Funcao principal"""
    print("PREPARANDO SISTEMA PARA DEPLOY")
    print("=" * 40)
    
    # Verificar arquivos
    if not check_files():
        print("ERRO: Arquivos necessarios nao encontrados")
        return False
    
    # Criar README
    create_readme()
    
    print("\nSISTEMA PRONTO PARA DEPLOY!")
    print("\nProximos passos:")
    print("1. git add .")
    print("2. git commit -m 'Sistema pronto para deploy'")
    print("3. git push origin main")
    print("4. Deploy no Vercel")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)