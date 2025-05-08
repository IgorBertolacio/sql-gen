# src/interfaces/api/run_api.py

"""
Script para iniciar o servidor da API.
"""

from .llm_controller import iniciar_servidor
from config.core.logging_config import setup_logging, get_logger
import os

if __name__ == "__main__":
    setup_logging(profile="api_server")
    logger = get_logger(__name__)

    # Determina a porta a partir da variável de ambiente ou usa 5000 como padrão
    porta = int(os.environ.get("PORT", 5000))
    env = os.environ.get("ENVIRONMENT", "development")
    
    logger.info(f"Iniciando servidor API no ambiente {env} (porta {porta})")
    
    try:
        # Inicia o servidor
        iniciar_servidor(porta=porta, modo_debug=(env == "development"))
    except Exception as e:
        logger.critical(f"Falha ao iniciar o servidor: {str(e)}")
        raise