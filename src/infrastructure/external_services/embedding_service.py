import google.generativeai as genai
import numpy as np
from typing import List, Optional
import logging
import os
# Importa configuração da API Gemini da estrutura do projeto.
from src.infrastructure.config.api.api_config import GeminiConfig

# Configura o logging para este serviço.
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class EmbeddingService:
    """
    Serviço para gerar embeddings de texto com Google GenAI.
    Garante compatibilidade com embeddings de scripts de indexação.
    Usa GeminiConfig para configurar a API.
    """

    # --- Configuração do Embedding ---
    # NOME DO MODELO: DEVE ser o mesmo do script de indexação (create_embeddings...).
    # Usar variável de ambiente (EMBEDDING_MODEL_NAME) é recomendado.
    _MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "models/text-embedding-004")
    # TIPO DE TAREFA: Define o propósito do embedding.
    _TASK_TYPE = "SEMANTIC_SIMILARITY"
    # ----------------------------------------------

    @staticmethod
    def embed_texts(texts: List[str]) -> Optional[np.ndarray]:
        """
        Gera embeddings L2-NORMALIZADOS para uma lista de textos.

        Usa o modelo e tipo de tarefa configurados (_MODEL_NAME, _TASK_TYPE).
        Garante inicialização da API via GeminiConfig.
        Replica a NORMALIZAÇÃO do script de indexação para consistência com o índice FAISS.

        Args:
            texts: Lista de strings (não vazias após filtragem) para gerar embeddings.

        Returns:
            Array NumPy (n, dim_embedding) com embeddings L2-normalizados (float32).
            None se a geração falhar, a lista de entrada for vazia/inválida, ou a API não inicializar.
        """
        # --- Garante configuração da API via GeminiConfig ---
        try:
            GeminiConfig.initialize() # Verifica se já inicializado ou inicializa.
            logger.debug("API Gemini inicializada (ou já estava).")
        except ValueError as e: # Erro específico: chave da API faltando?
            logger.error(f"Falha ao inicializar config Gemini (chave API?): {e}")
            return None
        except Exception as e_init: # Outros erros de inicialização.
            logger.error(f"Erro inesperado na config Gemini: {e_init}", exc_info=True)
            return None
        # --- API configurada globalmente ---

        # Validação da entrada
        if not texts:
            logger.warning("Chamada a embed_texts com lista vazia.")
            return None

        # Filtra strings vazias ou só com espaços.
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            logger.warning("Nenhum texto válido encontrado após filtragem.")
            return None

        logger.info(f"Gerando embeddings para {len(valid_texts)} textos. Modelo: '{EmbeddingService._MODEL_NAME}', Tarefa: '{EmbeddingService._TASK_TYPE}'.")

        try:
            # --- Chamada à API GenAI (usa config global) ---
            result = genai.embed_content(
                model=EmbeddingService._MODEL_NAME,
                content=valid_texts,
                task_type=EmbeddingService._TASK_TYPE
            )

            # --- Validação e Formatação do Resultado ---
            raw_embeddings = np.array(result['embedding'], dtype='float32')

            # Verifica forma do array retornado.
            if len(raw_embeddings.shape) != 2 or raw_embeddings.shape[0] != len(valid_texts):
                logger.error(f"Forma inesperada dos embeddings. Esperado: ({len(valid_texts)}, N), Recebido: {raw_embeddings.shape}")
                raise ValueError("Forma inconsistente retornada pela API.")

            # Verifica se o array está vazio.
            if raw_embeddings.size == 0:
                 logger.warning("API retornou array de embeddings vazio.")
                 return None

            # --- NORMALIZAÇÃO L2 (PASSO CRÍTICO - Igual ao script) ---
            logger.info(f"Normalizando {raw_embeddings.shape[0]} vetores de embedding.")
            # Calcula a norma L2 de cada vetor.
            norms = np.linalg.norm(raw_embeddings, axis=1, keepdims=True)
            # Evita divisão por zero para vetores nulos.
            norms[norms == 0] = 1e-10
            # Divide cada vetor pela sua norma L2.
            normalized_embeddings = raw_embeddings / norms

            logger.info(f"Gerados e normalizados {normalized_embeddings.shape[0]} embeddings de dimensão {normalized_embeddings.shape[1]}.")
            return normalized_embeddings

        # Tratamento genérico de erros da API ou processamento.
        except Exception as e:
            logger.error(f"Erro durante geração/normalização dos embeddings: {e}", exc_info=True)
            return None