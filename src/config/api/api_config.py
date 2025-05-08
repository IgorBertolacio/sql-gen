"""
Módulo de configuração para APIs externas.
Este módulo gerencia as chaves de API e configurações para serviços externos,
como o Google Gemini.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Any

load_dotenv()

class GeminiConfig: 
    _api_key: Optional[str] = None
    _is_initialized: bool = False
    
    @classmethod
    def get_api_key(cls) -> str:

        if cls._api_key is None:
            cls._api_key = os.getenv("LLM_API_KEY")
            
            if not cls._api_key:
                raise ValueError(
                    "A chave de API do Google Gemini não está configurada. "
                    "Por favor, defina a variável de ambiente 'LLM_API_KEY' "
                    "ou adicione-a ao arquivo .env."
                )
        
        return cls._api_key
    
    @classmethod
    def set_api_key(cls, api_key: str) -> None:

        cls._api_key = api_key
        cls._is_initialized = False
        
    @classmethod
    def is_configured(cls) -> bool:
        try:
            return bool(cls.get_api_key())
        except ValueError:
            return False
    
    @classmethod
    def initialize(cls) -> None:
        if not cls._is_initialized:
            api_key = cls.get_api_key()
            genai.configure(api_key=api_key)
            cls._is_initialized = True
    
    @classmethod
    def get_client(cls) -> Any:
        cls.initialize()
        return genai