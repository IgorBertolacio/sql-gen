"""
Script para iniciar o servidor da API.
"""

from src.interfaces.api.gemini_controller import iniciar_servidor
import os

if __name__ == "__main__":
    # Obtém a porta do ambiente ou usa 5000 como padrão
    porta = int(os.environ.get("PORT", 5000))
    
    print(f"Iniciando servidor na porta {porta}...")
    print("Pressione CTRL+C para encerrar.")
    
    # Inicia o servidor em modo de desenvolvimento
    iniciar_servidor(porta=porta, modo_debug=True)