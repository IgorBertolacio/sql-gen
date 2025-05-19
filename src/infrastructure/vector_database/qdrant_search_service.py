# src/infrastructure/vector_database/qdrant_search_service.py

import os
import numpy as np
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv
import traceback

class QdrantSearchService:
    def __init__(self, collection_name: str = "sql_metadados"):
        load_dotenv()
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if not qdrant_url:
            raise ValueError("QDRANT_URL não está definido no ambiente.")

        print(f"QdrantSearchService: Conectando ao Qdrant em {qdrant_url}...")
        try:
            self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            self.client.get_collections()
            print(f"QdrantSearchService: Conectado com sucesso. Usando coleção '{collection_name}'.")
        except Exception as e:
            print(f"QdrantSearchService CRITICAL ERROR: Falha ao conectar ao Qdrant: {e}")
            traceback.print_exc()
            raise ValueError(f"Não foi possível conectar ao Qdrant: {e}")

        self.collection_name = collection_name
        try:
            self.client.get_collection(collection_name=self.collection_name)
            print(f"QdrantSearchService: Coleção '{self.collection_name}' encontrada.")
        except Exception as e:
            detailed_error = f"Coleção '{self.collection_name}' não encontrada ou erro ao acessá-la: {e}"
            print(f"QdrantSearchService CRITICAL ERROR: {detailed_error}")
            traceback.print_exc()
            raise ValueError(detailed_error)

        collection_info = self.client.get_collection(collection_name=self.collection_name)
        if not collection_info.config.params.vectors:
             detailed_error = f"A coleção '{self.collection_name}' não parece ter uma configuração de vetor definida."
             print(f"QdrantSearchService CRITICAL ERROR: {detailed_error}")
             raise ValueError(detailed_error)

        self.vector_size = collection_info.config.params.vectors.size
        print(f"QdrantSearchService: Tamanho do vetor da coleção '{self.collection_name}' é {self.vector_size}.")


    def _ensure_l2_normalized(self, embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        return embeddings / norms

    def find_top_similar_tables(
        self,
        query_embeddings: np.ndarray,
        query_table_names: List[str],
        k: int = 3,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        if query_embeddings.size == 0 or len(query_table_names) == 0:
            print("QdrantSearchService: Embeddings de consulta ou nomes de tabelas vazios.")
            return []
        if query_embeddings.shape[0] != len(query_table_names):
            print(f"QdrantSearchService ERROR: Inconsistência - {query_embeddings.shape[0]} embeddings vs {len(query_table_names)} nomes.")
            return []
        if query_embeddings.shape[1] != self.vector_size:
            print(f"QdrantSearchService ERROR: Dimensão do embedding da consulta ({query_embeddings.shape[1]}) não corresponde à da coleção ({self.vector_size}).")
            return []

        print("QdrantSearchService: Verificando/Garantindo normalização dos embeddings de consulta (L2 norm)...")
        normalized_query_embeddings = self._ensure_l2_normalized(query_embeddings)
        print("QdrantSearchService: Normalização concluída/verificada.")

        all_results = []

        for i, query_table_name in enumerate(query_table_names):
            query_embedding = normalized_query_embeddings[i]
            print(f"QdrantSearchService: Buscando no Qdrant por '{query_table_name}' (top {k})...")
            try:
                # ****** PONTO CRÍTICO: REMOVIDO O PARÂMETRO `filter` DAQUI ******
                # Se você tinha um filtro aqui que causava o erro 403,
                # esta é a principal mudança.
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding.tolist(),
                    limit=k,
                    # score_threshold=score_threshold, # Descomente se quiser usar threshold
                    with_payload=True,
                    with_vectors=False # Geralmente não precisamos dos vetores dos resultados
                )

                matches_for_query = []
                for hit in search_result:
                    payload = hit.payload if hit.payload else {}
                    table_name_from_db = payload.get("name", "unknown_table_in_payload")
                    schema_from_db = payload.get("schema", "") # Adicionado para nome qualificado
                    full_table_name = f"{schema_from_db}.{table_name_from_db}" if schema_from_db else table_name_from_db

                    matches_for_query.append({
                        "table_name": full_table_name,
                        "similarity_score": hit.score,
                        "similarity_percentage": hit.score * 100, # Para métrica de similaridade cosseno normalizada
                        "content": payload.get("content", ""),
                        "payload_completo": payload
                    })
                all_results.append({
                    "query_table": query_table_name,
                    "matches": matches_for_query
                })
            except Exception as e:
                print(f"QdrantSearchService CRITICAL ERROR: Erro inesperado durante a busca para '{query_table_name}': {e}")
                traceback.print_exc()
                all_results.append({
                    "query_table": query_table_name,
                    "matches": [],
                    "error": str(e)
                })
        return all_results