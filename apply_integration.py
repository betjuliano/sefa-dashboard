"""
Script para aplicar a integração do novo sistema ao app.py

Este script modifica o app.py existente para usar o novo sistema de processamento
de questionários, mantendo compatibilidade com a interface atual.
"""

import os
import shutil
from datetime import datetime


def backup_app_py():
    """Cria backup do app.py atual"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"app_backup_{timestamp}.py"
    
    if os.path.exists("app.py"):
        shutil.copy2("app.py", backup_name)
        print(f"✅ Backup criado: {backup_name}")
        return backup_name
    else:
        print("❌ app.py não encontrado")
        return None


def read_file(filename):
    """Lê arquivo com encoding UTF-8"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Erro ao ler {filename}: {e}")
        return None


def write_file(filename, content):
    """Escreve arquivo com encoding UTF-8"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Arquivo atualizado: {filename}")
        return True
    except Exception as e:
        print(f"❌ Erro ao escrever {filename}: {e}")
        return False


def apply_integration():
    """Aplica a integração ao app.py"""
    print("🚀 Iniciando integração do novo sistema...")
    
    # 1. Fazer backup
    backup_file = backup_app_py()
    if not backup_file:
        return False
    
    # 2. Ler app.py atual
    app_content = read_file("app.py")
    if not app_content:
        return False
    
    print("📝 Aplicando modificações...")
    
    # 3. Adicionar import do novo sistema no início
    import_addition = """
# ===== NOVO SISTEMA DE PROCESSAMENTO =====
from app_integration import (
    app_integration,
    update_global_variables as new_update_global_variables,
    filter_by_question_set as new_filter_by_question_set,
    compute_metrics as new_compute_metrics,
    normalize_likert as new_normalize_likert,
    normalize_satisfaction as new_normalize_satisfaction,
    add_sidebar_enhancements
)
# ==========================================

"""
    
    # Encontrar onde adicionar o import (após os imports existentes)
    import_position = app_content.find("from dotenv import load_dotenv")
    if import_position != -1:
        # Encontrar o final da linha
        end_of_line = app_content.find("\n", import_position) + 1
        app_content = app_content[:end_of_line] + import_addition + app_content[end_of_line:]
        print("✅ Imports do novo sistema adicionados")
    else:
        print("⚠️ Posição de import não encontrada, adicionando no início")
        app_content = import_addition + app_content
    
    # 4. Substituir função update_global_variables
    old_function = '''def update_global_variables(question_set: str):
    """Atualiza as variáveis globais baseado no conjunto de questões selecionado"""
    global MAPPING, DIMENSIONS, LIKERT_ORDER, LIKERT_MAP, SAT_FIELD, SAT_MAP, PROFILE_FIELDS
    
    MAPPING = get_mapping_for_question_set(question_set)
    DIMENSIONS = MAPPING["dimensions"]
    LIKERT_ORDER = MAPPING["likert_order"]
    LIKERT_MAP = {k: v for k, v in MAPPING["likert_map"].items()}
    SAT_FIELD = MAPPING["satisfaction_field"]
    SAT_MAP = MAPPING["satisfaction_map"]
    PROFILE_FIELDS = MAPPING["profile_fields"]'''
    
    new_function = '''def update_global_variables(question_set: str):
    """Atualiza as variáveis globais baseado no conjunto de questões selecionado - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    new_update_global_variables(question_set)'''
    
    if old_function in app_content:
        app_content = app_content.replace(old_function, new_function)
        print("✅ Função update_global_variables substituída")
    else:
        print("⚠️ Função update_global_variables não encontrada para substituição")
    
    # 5. Substituir função normalize_likert
    old_normalize_likert = '''def normalize_likert(series: pd.Series) -> pd.Series:
    # Strip & standardize strings, map to numbers, keep NaN for "Não sei"
    s = series.astype(str).str.strip()
    s = s.replace("nan", np.nan)
    return s.map(LIKERT_MAP)'''
    
    new_normalize_likert = '''def normalize_likert(series: pd.Series) -> pd.Series:
    """Normaliza escala Likert - NOVO SISTEMA"""
    # Usar o novo ScaleConverter
    return new_normalize_likert(series)'''
    
    if old_normalize_likert in app_content:
        app_content = app_content.replace(old_normalize_likert, new_normalize_likert)
        print("✅ Função normalize_likert substituída")
    else:
        print("⚠️ Função normalize_likert não encontrada para substituição")
    
    # 6. Substituir função normalize_satisfaction
    old_normalize_satisfaction = '''def normalize_satisfaction(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().replace("nan", np.nan)
    return s.map(SAT_MAP)'''
    
    new_normalize_satisfaction = '''def normalize_satisfaction(series: pd.Series) -> pd.Series:
    """Normaliza escala de satisfação - NOVO SISTEMA"""
    # Usar o novo ScaleConverter
    return new_normalize_satisfaction(series)'''
    
    if old_normalize_satisfaction in app_content:
        app_content = app_content.replace(old_normalize_satisfaction, new_normalize_satisfaction)
        print("✅ Função normalize_satisfaction substituída")
    else:
        print("⚠️ Função normalize_satisfaction não encontrada para substituição")
    
    # 7. Substituir função filter_by_question_set (mais complexa)
    # Encontrar o início da função
    filter_start = app_content.find("def filter_by_question_set(df: pd.DataFrame, question_set: str):")
    if filter_start != -1:
        # Encontrar o final da função (próxima função ou final do arquivo)
        next_def = app_content.find("\ndef ", filter_start + 1)
        if next_def == -1:
            next_def = len(app_content)
        
        # Substituir toda a função
        new_filter_function = '''def filter_by_question_set(df: pd.DataFrame, question_set: str):
    """Filtra o dataframe baseado no conjunto de questões selecionado - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    return new_filter_by_question_set(df, question_set)

'''
        
        app_content = app_content[:filter_start] + new_filter_function + app_content[next_def:]
        print("✅ Função filter_by_question_set substituída")
    else:
        print("⚠️ Função filter_by_question_set não encontrada para substituição")
    
    # 8. Substituir função compute_metrics (mais complexa)
    compute_start = app_content.find("def compute_metrics(df: pd.DataFrame, goal: float):")
    if compute_start != -1:
        # Encontrar o final da função
        next_def = app_content.find("\ndef ", compute_start + 1)
        if next_def == -1:
            # Procurar por comentário de seção
            next_section = app_content.find("\n# ", compute_start + 1)
            if next_section != -1:
                next_def = next_section
            else:
                next_def = len(app_content)
        
        new_compute_function = '''def compute_metrics(df: pd.DataFrame, goal: float):
    """Calcula métricas do questionário - NOVO SISTEMA"""
    # Usar o novo sistema integrado
    return new_compute_metrics(df, goal)

'''
        
        app_content = app_content[:compute_start] + new_compute_function + app_content[next_def:]
        print("✅ Função compute_metrics substituída")
    else:
        print("⚠️ Função compute_metrics não encontrada para substituição")
    
    # 9. Adicionar melhorias à barra lateral
    # Encontrar onde adicionar (após o seletor de conjunto de questões)
    sidebar_position = app_content.find("st.session_state.question_set = question_set")
    if sidebar_position != -1:
        end_of_line = app_content.find("\n", sidebar_position) + 1
        sidebar_addition = "\n# Adicionar melhorias do novo sistema\nadd_sidebar_enhancements()\n"
        app_content = app_content[:end_of_line] + sidebar_addition + app_content[end_of_line:]
        print("✅ Melhorias da barra lateral adicionadas")
    else:
        print("⚠️ Posição para melhorias da barra lateral não encontrada")
    
    # 10. Salvar arquivo modificado
    success = write_file("app.py", app_content)
    
    if success:
        print("\n🎉 Integração aplicada com sucesso!")
        print(f"📁 Backup salvo em: {backup_file}")
        print("\n✅ Modificações aplicadas:")
        print("  • Imports do novo sistema adicionados")
        print("  • Função update_global_variables substituída")
        print("  • Função normalize_likert substituída")
        print("  • Função normalize_satisfaction substituída")
        print("  • Função filter_by_question_set substituída")
        print("  • Função compute_metrics substituída")
        print("  • Melhorias da barra lateral adicionadas")
        print("\n🚀 O app.py agora usa o novo sistema de processamento!")
        print("\n📋 Para testar:")
        print("  1. Execute: streamlit run app.py")
        print("  2. Teste os filtros da barra lateral")
        print("  3. Verifique as validações de estrutura")
        print("  4. Observe as melhorias de performance")
        
        return True
    else:
        print("\n❌ Falha ao aplicar integração")
        return False


def rollback_integration(backup_file):
    """Desfaz a integração restaurando o backup"""
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, "app.py")
        print(f"✅ Integração desfeita. app.py restaurado do backup: {backup_file}")
        return True
    else:
        print(f"❌ Arquivo de backup não encontrado: {backup_file}")
        return False


if __name__ == "__main__":
    print("🔧 Script de Integração do Novo Sistema de Processamento")
    print("=" * 60)
    
    # Verificar se arquivos necessários existem
    required_files = ["app.py", "app_integration.py", "core/questionnaire_processor.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Arquivos necessários não encontrados:")
        for f in missing_files:
            print(f"  • {f}")
        print("\nCertifique-se de que todos os arquivos estão presentes.")
        exit(1)
    
    print("✅ Todos os arquivos necessários encontrados")
    print("\n⚠️  ATENÇÃO: Este script irá modificar o app.py")
    print("Um backup será criado automaticamente.")
    
    response = input("\nDeseja continuar? (s/N): ").lower().strip()
    
    if response in ['s', 'sim', 'y', 'yes']:
        success = apply_integration()
        
        if success:
            print("\n" + "=" * 60)
            print("🎯 INTEGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("\nO sistema agora oferece:")
            print("✅ Processamento robusto de escalas Likert")
            print("✅ Validação automática de estrutura de dimensões")
            print("✅ Filtros da barra lateral aprimorados")
            print("✅ Cache inteligente para melhor performance")
            print("✅ Tratamento de erros melhorado")
            print("✅ Relatórios detalhados de processamento")
        else:
            print("\n❌ Integração falhou. Verifique os erros acima.")
    else:
        print("❌ Integração cancelada pelo usuário.")