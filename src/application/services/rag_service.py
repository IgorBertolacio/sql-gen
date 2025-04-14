"""
Serviço para orquestrar o fluxo de execução do RAG.
Este módulo integra as instruções SQL com o serviço LLM.
"""

from typing import Dict, Any, Optional
from src.infrastructure.config.prompts.base_instructions import BaseInstructions
from src.infrastructure.config.prompts.sql_instructions import SQLInstructions
from src.infrastructure.external_services.gemini_service import LLMService

class RAGService:
    """
    Serviço que orquestra o fluxo de execução do RAG.
    Responsável por controloar toda a arquitetura da RAG para optimizar consultas SQL
    """   
    @staticmethod
    def extrair_estrutura_sql(prompt_usuario: str) -> Dict[str, Any]:
        """
        Extrai informações estruturais do prompt do usuário para SQL.
        
        Args:
            prompt_usuario: O prompt fornecido pelo usuário.
            
        Returns:
            Um dicionário contendo a resposta do Gemini com informações estruturais.
        """
        # Obtém as instruções para extração de informações
        instrucoes_extracao = BaseInstructions.get_stract_infos_instruction()
        
        # Combina as instruções com o prompt do usuário
        prompt_completo = f"""
        {instrucoes_extracao}
        
        Prompt do usuário:
        {prompt_usuario} 
        """
        
         
        resultado = LLMService.processar_prompt(prompt_completo)
        
        return resultado