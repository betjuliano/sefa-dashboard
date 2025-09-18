"""
Script simples para commit e push
Sem emojis para compatibilidade Windows
"""
import subprocess
import sys

def run_command(cmd, desc):
    """Executa comando e mostra resultado"""
    print(f"Executando: {desc}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"OK: {desc}")
            if result.stdout.strip():
                print(f"  {result.stdout.strip()}")
            return True
        else:
            print(f"ERRO: {desc}")
            if result.stderr.strip():
                print(f"  {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"ERRO: {desc} - {str(e)}")
        return False

def main():
    """Funcao principal"""
    print("ENVIANDO SISTEMA PARA GITHUB")
    print("=" * 40)
    
    # Verificar se e repositorio git
    if not run_command("git status", "Verificando repositorio"):
        print("ERRO: Nao e um repositorio Git")
        return False
    
    # Adicionar arquivos
    if not run_command("git add .", "Adicionando arquivos"):
        return False
    
    # Commit
    commit_msg = "feat: Sistema de filtros implementado e pronto para deploy"
    if not run_command(f'git commit -m "{commit_msg}"', "Fazendo commit"):
        print("INFO: Pode nao haver mudancas para commit")
    
    # Push
    if run_command("git push origin main", "Push para main"):
        print("SUCESSO: Enviado para main")
    elif run_command("git push origin master", "Push para master"):
        print("SUCESSO: Enviado para master")
    else:
        print("ERRO: Falha ao enviar para GitHub")
        return False
    
    print("\n" + "=" * 40)
    print("SISTEMA ENVIADO PARA GITHUB!")
    print("\nPROXIMOS PASSOS PARA VERCEL:")
    print("1. Acesse vercel.com")
    print("2. Conecte seu repositorio GitHub")
    print("3. Deploy automatico")
    print("4. Sistema funcionara com filtros da barra lateral")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)