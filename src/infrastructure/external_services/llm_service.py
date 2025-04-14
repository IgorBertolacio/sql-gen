"""
Serviço para interação com a LLM
"""

from src.infrastructure.config.api.api_config import GeminiConfig
import time
from typing import Dict, Any, Optional

class LLMService:
    """ 
    Serviço para interagir com a LLM
    """
    
    @staticmethod
    def processar_prompt(prompt: str, modelo: str = 'gemini-2.0-flash') -> Dict[str, Any]:
        """
        Envia um prompt para a API do Gemini e retorna a resposta junto com informações de uso.
        
        Args:
            prompt: O prompt a ser enviado para a API.
            modelo: O modelo LLM a ser utilizado. Padrão é 'gemini-2.0-flash'.
            
        Returns: 
            Um dicionário contendo a resposta e informações sobre o uso de tokens.
        """
        # Inicializa o cliente Gemini
        genai = GeminiConfig.get_client()
        
        # Obtém o modelo
        modelo_gemini = genai.GenerativeModel(modelo)
        
        # Registra o tempo de início
        tempo_inicio = time.time()
        
        # Envia a solicitação
        resposta = modelo_gemini.generate_content(prompt)
        
        # Registra o tempo de término
        tempo_fim = time.time()
        
        # Calcula o tempo de resposta em segundos
        tempo_resposta = tempo_fim - tempo_inicio
        
        # Obtém informações de uso (tokens)
        info_uso = resposta._result.usage_metadata
        tokens_entrada = info_uso.prompt_token_count if info_uso else "Não disponível"
        tokens_saida = info_uso.candidates_token_count if info_uso else "Não disponível"
        tokens_total = info_uso.total_token_count if info_uso else "Não disponível"
        
        # Retorna a resposta e informações de uso
        return {
            "resposta": resposta.text,
            "uso": {
                "tokens_entrada": tokens_entrada,
                "tokens_saida": tokens_saida,
                "tokens_total": tokens_total,
                "tempo_resposta": f"{tempo_resposta:.2f} segundos"
            }
        }