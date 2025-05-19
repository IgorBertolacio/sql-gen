# src/infrastructure/vector_database/search_service.py

import numpy as np
from typing import List, Dict, Any
from src.infrastructure.vector_database.qdrant_search_service import QdrantSearchService
import traceback # Mantido para log de erros inesperados

class SearchService:
    """
    Serviço de fachada para buscar TABELAS similares.
    Delega a busca real para o serviço Qdrant configurado.
    """

    # A instância do QdrantSearchService pode ser criada a cada chamada (simples)
    # ou gerenciada de forma mais sofisticada se necessário (e.g., injeção de dependência)
    _qdrant_searcher_instance = None

    @staticmethod
    def _get_qdrant_service() -> QdrantSearchService:
        """
        Obtém ou cria uma instância do QdrantSearchService.
        Lida com a inicialização e possíveis erros de conexão/configuração.
        """
        # Implementação simples: cria uma nova instância a cada vez.
        # Isso garante que as credenciais mais recentes do .env sejam usadas
        # e evita gerenciar o ciclo de vida da conexão no nível do SearchService.
        try:
            print("SearchService: Inicializando QdrantSearchService...")
            qdrant_service = QdrantSearchService()
            print("SearchService: QdrantSearchService inicializado com sucesso.")
            return qdrant_service
        except ValueError as ve:
            print(f"SearchService CRITICAL ERROR: Falha na configuração do QdrantSearchService: {ve}")
            traceback.print_exc()
            raise # Re-lança o erro de configuração para indicar falha
        except Exception as e:
            print(f"SearchService CRITICAL ERROR: Falha ao inicializar QdrantSearchService: {e}")
            traceback.print_exc()
            raise # Re-lança outros erros de inicialização

    @staticmethod
    def find_top_similar_tables(
        query_embeddings: np.ndarray,
        query_table_names: List[str],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Busca as 'k' tabelas mais similares usando o QdrantSearchService.

        Args:
            query_embeddings: Um array NumPy (N, D) contendo os embeddings
                              (idealmente L2 NORMALIZADOS, pois o QdrantService fará isso de qualquer forma)
                              para N nomes de tabelas extraídos da consulta do usuário.
            query_table_names: Uma lista de strings (N) com os nomes originais das tabelas
                               correspondentes aos query_embeddings.
            k: O número de vizinhos mais próximos a serem retornados para cada consulta.

        Returns:
            Uma lista de dicionários. Cada dicionário representa uma tabela de consulta
            e contém uma lista das tabelas mais similares encontradas via Qdrant.
            Retorna uma lista vazia em caso de erro durante a inicialização do serviço Qdrant
            ou durante a busca.
        """
        # Validação de entrada (mantida para falha rápida)
        print(f"SearchService: Recebido {len(query_table_names)} tabelas de consulta para busca via Qdrant.")
        if query_embeddings.size == 0 or len(query_table_names) == 0:
             print("SearchService: Embeddings de consulta ou nomes de tabelas vazios. Retornando lista vazia.")
             return []
        if query_embeddings.shape[0] != len(query_table_names):
             print(f"SearchService ERROR: Inconsistência - {query_embeddings.shape[0]} embeddings vs {len(query_table_names)} nomes.")
             return []

        try:
            # 1. Obter (ou criar) a instância do serviço Qdrant
            qdrant_searcher = SearchService._get_qdrant_service()

            # 2. Delegar a busca para o serviço Qdrant
            # A normalização e a verificação de dimensão são tratadas dentro do QdrantSearchService
            print(f"SearchService: Delegando busca para QdrantSearchService (k={k})...")
            results = qdrant_searcher.find_top_similar_tables(
                query_embeddings=query_embeddings,
                query_table_names=query_table_names,
                k=k
            )
            print(f"SearchService: Busca delegada concluída. Retornando {len(results)} resultados.")
            return results

        # Captura erros que podem ocorrer na inicialização do _get_qdrant_service
        # ou dentro da chamada find_top_similar_tables do qdrant_searcher
        except (ValueError, Exception) as e:
            print(f"SearchService CRITICAL ERROR: Erro durante a operação de busca via Qdrant: {e}")
            # O traceback já foi impresso em _get_qdrant_service ou será impresso
            # se o erro ocorrer na chamada find_top_similar_tables do qdrant_searcher
            if not isinstance(e, ValueError): # Evita duplicar o traceback para ValueErrors já tratados
                 traceback.print_exc()
            return [] # Retorna lista vazia em caso de erro

#