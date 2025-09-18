"""
Script simples para preparar projeto para GitHub
"""

import os
import subprocess
import sys

def check_files():
    """Verifica arquivos necessarios"""
    print("Verificando arquivos...")
    
    required = [
        'requirements.txt',
        'vercel.json', 
        'README.md',
        '.gitignore',
        'app.py',
        'app_integration.py'
    ]
    
    missing = []
    for file_path in required:
        if os.path.exists(file_path):
            print(f"OK: {file_path}")
        else:
            print(f"FALTA: {file_path}")
            missing.append(file_path)
    
    return len(missing) == 0

def test_basic():
    """Teste basico"""
    print("\nTestando sistema...")
    
    try:
        # Desabilitar emojis
        os.environ['DISABLE_EMOJIS'] = 'true'
        
        from core import QuestionnaireProcessor
        processor = QuestionnaireProcessor()
        
        # Teste simples
        config = processor.load_configuration("base20")
        print("OK: Sistema funcionando")
        
        return True
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return False

def git_add_commit():
    """Adiciona e faz commit"""
    print("\nPreparando Git...")
    
    try:
        # Verificar se é repo Git
        if not os.path.exists('.git'):
            print("Inicializando repositorio Git...")
            subprocess.run(['git', 'init'], check=True)
        
        # Adicionar arquivos
        print("Adicionando arquivos...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Verificar se há mudanças
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], capture_output=True)
        if result.returncode == 0:
            print("Nenhuma mudanca para commitar")
            return True
        
        # Fazer commit
        commit_msg = "feat: Sistema de filtros implementado - Pronto para Vercel"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        print("OK: Commit realizado")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERRO Git: {e}")
        return False
    except Exception as e:
        print(f"ERRO: {e}")
        return False

def show_next_steps():
    """Mostra proximos passos"""
    print("\n" + "="*50)
    print("PROJETO PREPARADO PARA GITHUB E VERCEL!")
    print("="*50)
    
    print("\nPROXIMOS PASSOS:")
    print("\n1. PUSH PARA GITHUB:")
    print("   git push origin main")
    print("   (ou git push origin master)")
    
    print("\n2. DEPLOY NO VERCEL:")
    print("   - Acesse: https://vercel.com")
    print("   - Conecte seu repositorio GitHub")
    print("   - Clique em 'Deploy'")
    print("   - Aguarde o build automatico")
    
    print("\n3. CONFIGURACOES VERCEL:")
    print("   - Framework: Other")
    print("   - Build Command: (vazio)")
    print("   - Install Command: pip install -r requirements.txt")
    
    print("\n4. TESTE NO VERCEL:")
    print("   - Acesse a URL gerada")
    print("   - Teste os filtros da barra lateral")
    print("   - Verifique reorganizacao das dimensoes")
    
    print("\nARQUIVOS CRIADOS:")
    print("   - requirements.txt")
    print("   - vercel.json")
    print("   - .streamlit/config.toml")
    print("   - README.md")
    print("   - .gitignore")

def main():
    """Funcao principal"""
    print("PREPARANDO PROJETO PARA GITHUB E VERCEL")
    print("="*50)
    
    # Verificar arquivos
    if not check_files():
        print("\nERRO: Arquivos necessarios faltando")
        return False
    
    # Testar sistema
    if not test_basic():
        print("\nERRO: Sistema nao esta funcionando")
        return False
    
    # Git operations
    if not git_add_commit():
        print("\nERRO: Problemas com Git")
        return False
    
    # Mostrar próximos passos
    show_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "="*50)
        print("PREPARACAO CONCLUIDA COM SUCESSO!")
        print("EXECUTE: git push origin main")
        exit(0)
    else:
        print("\n" + "="*50)
        print("PREPARACAO FALHOU")
        exit(1)