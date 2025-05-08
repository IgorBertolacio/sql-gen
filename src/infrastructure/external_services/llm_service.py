# infrastructure/external_services/llm_service.py
from config.api.api_config import GeminiConfig
from config.core.logging_config import get_logger

logger = get_logger(__name__)

class LLMService:
    """
    Serviço direto para processar prompts com a LLM.
    Usa níveis pré-definidos ('fraco', 'medio', 'forte', 'extremo') e retorna apenas o texto da resposta.
    """
    MODELOS = {
        "fraco": "gemini-2.0-flash-lite",
        "medio": "gemini-2.0-flash",
        "forte": "gemini-2.5-flash-preview-04-17",
        "extremo": "gemini-2.5-pro-preview-05-06"
    }

    @staticmethod
    def processar_prompt(prompt: str, nivel_modelo: str = "medio") -> str:
        nivel = nivel_modelo.lower()
        modelo = LLMService.MODELOS.get(nivel, LLMService.MODELOS["medio"])
        
        logger.info(f"\n[LLM SERVICE] Enviando prompt para o modelo: {modelo} (nível: {nivel})")
        
        try:
            genai = GeminiConfig.get_client()
            resposta = genai.GenerativeModel(modelo).generate_content(prompt)
            return resposta.text if hasattr(resposta, 'text') else ""
        except Exception as e:
            logger.error(f"\n[LLM SERVICE] Erro ao processar prompt: {e}")
            return ""
