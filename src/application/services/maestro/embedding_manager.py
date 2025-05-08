# src/application/services/maestro/embedding_manager.py

from typing import Dict, Any, List, Optional
import numpy as np
import logging

from infrastructure.external_services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """
    Gerencia a etapa de geração de embeddings do processo RAG.
    Responsável por transformar as tabelas extraídas em embeddings para busca vetorial.
    """
    
    @staticmethod
    def generate_embeddings_for_tables(tables_list: List[str]) -> Dict[str, Any]:
        """
        Gera embeddings para uma lista de tabelas.
        
        Args:
            tables_list: Lista de nomes de tabelas para gerar embeddings.
            
        Returns:
            Um dicionário contendo os embeddings gerados e informações relacionadas.
        """
        logger.info(f"\n[EmbeddingManager]\nGerando embeddings para {len(tables_list)} tabelas...")
        
        try:
            # Verifica se há tabelas para processar
            if not tables_list:
                logger.info("\n[EmbeddingManager]\nNenhuma tabela para gerar embeddings. Pulando etapa.")
                return {
                    "sucesso": True,
                    "embeddings": None,
                    "similar_tables_result": []  # Lista vazia para evitar erros posteriores
                }
            
            # Gera embeddings para as tabelas
            embedding_result_array = EmbeddingService.embed_texts(tables_list)
            
            # Verifica se os embeddings foram gerados corretamente
            if not isinstance(embedding_result_array, np.ndarray) or embedding_result_array.size == 0:
                logger.warning(f"\n[EmbeddingManager]\nFalha ao gerar embeddings para as tabelas: {tables_list}. Continuando sem busca vetorial.")
                return {
                    "sucesso": True,
                    "embeddings": None,
                    "similar_tables_result": []  # Lista vazia para evitar erros posteriores
                }
            
            # Embeddings gerados com sucesso
            logger.info(f"\n[EmbeddingManager]\nEmbeddings gerados com sucesso: shape {embedding_result_array.shape}")
            return {
                "sucesso": True,
                "embeddings": embedding_result_array,
                "tabelas": tables_list
            }
            
        except Exception as e:
            logger.error(f"\n[EmbeddingManager]\nErro durante a geração de embeddings: {str(e)}")
            return {
                "sucesso": False,
                "erro": "Erro durante a geração de embeddings",
                "detalhes": str(e)
            }