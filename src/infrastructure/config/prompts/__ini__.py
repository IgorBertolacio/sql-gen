"""
Pacote para armazenar instruções e prompts para a LLM.
Este módulo contém diferentes tipos de instruções que serão usadas
para controlar as respostas da LLM em vários contextos.
"""

from src.infrastructure.config.prompts.base_instructions import BaseInstructions
from src.infrastructure.config.prompts.sql_instructions import SQLInstructions

__all__ = ["BaseInstructions", "SQLInstructions"]