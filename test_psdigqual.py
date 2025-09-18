"""
Teste simples para verificar se o PSDigQual está funcionando
"""
import subprocess
import time
import sys
import os

def test_psdigqual():
    """Testa se o projeto PSDigQual está funcionando"""
    print("TESTANDO PROJETO PSDIGQUAL")
    print("=" * 40)
    
    # Verificar se a pasta existe
    if not os.path.exists("PSDigQual"):
        print("ERRO: Pasta PSDigQual nao encontrada")
        return False
    
    print("OK: Pasta PSDigQual encontrada")
    
    # Verificar se package.json existe
    if not os.path.exists("PSDigQual/package.json"):
        print("ERRO: package.json nao encontrado")
        return False
    
    print("OK: package.json encontrado")
    
    # Verificar se node_modules existe
    if not os.path.exists("PSDigQual/node_modules"):
        print("AVISO: node_modules nao encontrado, executando npm install...")
        try:
            result = subprocess.run(
                "npm install", 
                shell=True, 
                cwd="PSDigQual",
                capture_output=True, 
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print("OK: npm install executado com sucesso")
            else:
                print(f"ERRO: npm install falhou - {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("ERRO: npm install demorou muito tempo")
            return False
        except Exception as e:
            print(f"ERRO: Falha ao executar npm install - {str(e)}")
            return False
    else:
        print("OK: node_modules encontrado")
    
    # Verificar se consegue fazer build
    print("Testando build do projeto...")
    try:
        result = subprocess.run(
            "npm run build", 
            shell=True, 
            cwd="PSDigQual",
            capture_output=True, 
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("OK: Build executado com sucesso")
        else:
            print(f"ERRO: Build falhou - {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("ERRO: Build demorou muito tempo")
        return False
    except Exception as e:
        print(f"ERRO: Falha ao executar build - {str(e)}")
        return False
    
    print("\n" + "=" * 40)
    print("SUCESSO: PSDigQual esta funcionando!")
    print("\nPara executar o projeto:")
    print("1. cd PSDigQual")
    print("2. npm run dev")
    print("3. Acesse http://localhost:5173")
    
    return True

if __name__ == "__main__":
    success = test_psdigqual()
    sys.exit(0 if success else 1)