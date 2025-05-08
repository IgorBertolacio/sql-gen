# src/infrastructure/external_services/embedding_service.py

import google.generativeai as genai
import numpy as np
from typing import List, Optional
import logging
import os
from config.api.api_config import GeminiConfig

logger = logging.getLogger(__name__)
# Ensures basicConfig is called only if no handlers are already configured for this logger or root.
# This makes it safe if another module (like llm_controller) already set up global logging.
if not logging.getLogger().hasHandlers(): # Check root logger
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class EmbeddingService:
    """
    Serviço para gerar embeddings de texto com Google GenAI.
    """
    _MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "models/text-embedding-004")
    
    _TASK_TYPE = "RETRIEVAL_QUERY" 

    @staticmethod
    def embed_texts(texts: List[str]) -> Optional[np.ndarray]:
        """
        Gera embeddings L2-NORMALIZADOS para uma lista de textos.
        Usa o modelo e tipo de tarefa (_TASK_TYPE) definidos na classe.
        """
        try:
            GeminiConfig.initialize()
            logger.debug("\n[Embedding Service]\nAPI Gemini inicializada (ou já estava).")
        except ValueError as e:
            logger.error(f"\n[Embedding Service]\nFalha ao inicializar config Gemini (chave API?): {e}")
            return None
        except Exception as e_init:
            logger.error(f"\n[Embedding Service]\nErro inesperado na config Gemini: {e_init}", exc_info=True)
            return None

        if not texts:
            logger.warning("\n[Embedding Service]\nChamada a embed_texts com lista vazia.")
            return None
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            logger.warning("\n[Embedding Service]\nNenhum texto válido encontrado após filtragem.")
            return None

        logger.info(f"\n[Embedding Service]\nGerando embeddings para {len(valid_texts)} textos. Modelo: '{EmbeddingService._MODEL_NAME}', Tarefa: '{EmbeddingService._TASK_TYPE}'.")

        try:
            result = genai.embed_content(
                model=EmbeddingService._MODEL_NAME,
                content=valid_texts,
                task_type=EmbeddingService._TASK_TYPE
            )
            raw_embeddings = np.array(result['embedding'], dtype='float32')

            if len(raw_embeddings.shape) != 2 or raw_embeddings.shape[0] != len(valid_texts):
                logger.error(f"\n[Embedding Service]\nForma inesperada dos embeddings. Esperado: ({len(valid_texts)}, N), Recebido: {raw_embeddings.shape}")
                raise ValueError("Forma inconsistente retornada pela API.")
            if raw_embeddings.size == 0:
                 logger.warning("\n[Embedding Service]\nAPI retornou array de embeddings vazio.")
                 return None

            logger.info(f"\n[Embedding Service]\nNormalizando {raw_embeddings.shape[0]} vetores de embedding.")
            norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10
            normalized_embeddings = raw_embeddings / norms

            logger.info(f"\n[Embedding Service]\nGerados e normalizados {normalized_embeddings.shape[0]} embeddings de dimensão {normalized_embeddings.shape[1]}.")
            return normalized_embeddings
        except Exception as e:
            logger.error(f"\n[Embedding Service]\nErro durante geração/normalização dos embeddings: {e}", exc_info=True)
            return None