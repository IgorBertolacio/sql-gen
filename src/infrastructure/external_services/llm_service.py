from typing import Dict, Any
from src.infrastructure.config.api.api_config import GeminiConfig

class LLMService:
    """ 
    Serviço para interagir com a LLM
    """

    @staticmethod
    def get_api_response(prompt: str, modelo: str = 'gemini-2.0-flash'):
        """
        Retorna o objeto de resposta bruto da API do Gemini.
        """
        genai = GeminiConfig.get_client()
        modelo_gemini = genai.GenerativeModel(modelo)
        resposta = modelo_gemini.generate_content(prompt)
        return resposta

    @staticmethod
    def get_usage_data(resposta_api) -> dict:
        """
        Extrai apenas os dados de uso (tokens, tempo, etc) da resposta da API Gemini.
        """
        info_uso = resposta_api._result.usage_metadata
        return {
            "tokens_entrada": info_uso.prompt_token_count if info_uso else "Não disponível",
            "tokens_saida": info_uso.candidates_token_count if info_uso else "Não disponível",
            "tokens_total": info_uso.total_token_count if info_uso else "Não disponível"
        }

    @staticmethod
    def get_response_text(resposta_api) -> str:
        """
        Extrai apenas o texto da resposta da API Gemini.
        """
        return resposta_api.text

    @staticmethod
    def processar_prompt(prompt: str, modelo: str = 'gemini-2.0-flash') -> Dict[str, Any]:
        """
        (Mantido para compatibilidade) Envia um prompt e retorna resposta, uso e tempo.
        """
        import time
        tempo_inicio = time.time()
        resposta_api = LLMService.get_api_response(prompt, modelo)
        tempo_fim = time.time()
        tempo_resposta = tempo_fim - tempo_inicio

        return {
            "resposta": LLMService.get_response_text(resposta_api),
            "uso": {
                **LLMService.get_usage_data(resposta_api),
                "tempo_resposta": f"{tempo_resposta:.2f} segundos"
            }
        }