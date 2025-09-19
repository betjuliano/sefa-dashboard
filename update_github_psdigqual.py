"""
Script para atualizar o GitHub com as melhorias do PSDigQual
"""
import subprocess
import sys
import os

def run_git_command(command, description, cwd="PSDigQual"):
    """Executa comando git e mostra resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, te