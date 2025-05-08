# src/application/services/maestro/search_manager.py

from typing import Dict, Any, List, Optional
import numpy as np
import logging

from infrastructure.vector_database.search_service import SearchService

logger = logging.getLogger(__name__)

class SearchManager:
    """
    Gerencia a etapa de busca vetorial do processo RAG.
    Responsável por encontrar tabelas similares no índice vetorial.
    """
    
    @staticmethod
    def find_similar_tables(query_embeddings: Optional[np.ndarray], 
                           table_names: List[str], 
                           k: int = 5) -> Dict[str, Any]:
        """
        Busca tabelas similares no índice vetorial.
        
        Args:
            query_embeddings: Array de embeddings das tabelas de consulta.
            table_names: Lista de nomes das tabelas de consulta.
            k: Número máximo de resultados por consulta.
            
        Returns:
            Um dicionário contendo os resultados da busca ou informação de erro.
        """
        try:
            # Verifica se os embeddings foram fornecidos
            if query_embeddings is None:
                logger.info("\n[SEARCH MANAGER]\nNenhum embedding fornecido. Pulando busca vetorial.")
                return {
                    "sucesso": True,
                    "resultados": []
                }
            
            # Realiza a busca vetorial
            logger.info(f"\n[SEARCH MANAGER]\nBuscando tabelas similares no índice vetorial para {len(table_names)} tabelas...")
            similar_tables_result = SearchService.find_top_similar_tables(
                query_embeddings=query_embeddings,
                query_table_names=table_names,
                k=k
            )
            
            # Log dos resultados
            logger.info(f"\n[SEARCH MANAGER]\nBusca vetorial concluída. {len(similar_tables_result)} resultados obtidos.")

            # Log detalhado mostrando as correspondências encontradas
            for resultado in similar_tables_result:
                tabela_original = resultado.get("query_table", "")
                matches = resultado.get("matches", [])
                
                if matches:
                    tabelas_encontradas = []
                    for match in matches:
                        table_name = match.get("table_name", "")
                        similarity = match.get("similarity_percentage", 0)
                        tabelas_encontradas.append(f"{table_name} ({similarity:.2f}%)")
                    
                    logger.info(f"\n[SEARCH MANAGER]\nPara tabela mencionada '{tabela_original}' foram encontradas: {', '.join(tabelas_encontradas)}")
                else:
                    logger.info(f"\n[SEARCH MANAGER]\nNenhuma tabela similar encontrada para '{tabela_original}'")
           
            return {
                "sucesso": True,
                "resultados": similar_tables_result
            }
            
        except Exception as e:
            logger.error(f"\n[SEARCH MANAGER]\nErro durante a busca vetorial: {str(e)}")
            return {
                "sucesso": False,
                "erro": "Erro durante a busca vetorial",
                "detalhes": str(e),
                "resultados": []  # Retorna lista vazia para evitar erros posteriores
            }