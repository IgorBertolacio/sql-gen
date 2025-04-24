# src/infrastructure/vector_database/search_service.py
import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Tuple, Any
from src.infrastructure.persistence.index_loader import IndexLoader

class SearchService:
    """
    Serviço para buscar TABELAS similares
    em um índice FAISS usando embeddings de consulta.
    """

    @staticmethod
    def find_top_similar_tables(
        query_embeddings: np.ndarray,
        query_table_names: List[str],
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Busca no índice FAISS carregado as 'k' tabelas mais similares para cada embedding de consulta.

        Args:
            query_embeddings: Um array NumPy (N, D) contendo os embeddings L2 NORMALIZADOS
                              para N nomes de tabelas extraídos da consulta do usuário.
            query_table_names: Uma lista de strings (N) com os nomes originais das tabelas
                               correspondentes aos query_embeddings.
            k: O número de vizinhos mais próximos a serem retornados para cada consulta.

        Returns:
            Uma lista de dicionários. Cada dicionário representa uma tabela de consulta
            e contém uma lista das tabelas mais similares encontradas no índice.
        """
        results = []
        faiss_index = None
        metadata_list = None

        # Validação de entrada
        print(f"SearchService: Recebido {len(query_table_names)} tabelas de consulta para busca.")
        if query_embeddings.size == 0 or len(query_table_names) == 0:
             print("SearchService: Embeddings de consulta ou nomes de tabelas vazios. Retornando lista vazia.")
             return []
        if query_embeddings.shape[0] != len(query_table_names):
             print(f"SearchService ERROR: Inconsistência - {query_embeddings.shape[0]} embeddings vs {len(query_table_names)} nomes.")
             return []

        try:
            # 1. Carregar Índice e Metadados
            print("SearchService: Carregando índice FAISS e metadados...")
            faiss_index, metadata_list = IndexLoader.load_index()
            print(f"SearchService: Índice carregado com {faiss_index.ntotal} vetores (Dim: {faiss_index.d}). Metadados: {len(metadata_list)} entradas.")

            if faiss_index.ntotal == 0 or not metadata_list:
                print("SearchService ERROR: Índice FAISS ou metadados vazios. Não é possível buscar.")
                return []

            if faiss_index.ntotal != len(metadata_list):
                print(f"SearchService ERROR: Inconsistência carregada - Índice ({faiss_index.ntotal}) != Metadados ({len(metadata_list)}).")
                return []

            # 2. Verificar Dimensão do Embedding da Consulta
            query_dim = query_embeddings.shape[1]
            index_dim = faiss_index.d
            if query_dim != index_dim:
                print(f"SearchService ERROR: Dimensão do embedding da consulta ({query_dim}) não corresponde à dimensão do índice ({index_dim}).")
                return []

            # 3. Garantir Normalização L2 dos Embeddings da Consulta
            print("SearchService: Verificando/Garantindo normalização dos embeddings de consulta (L2 norm)...")
            norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1e-10 # Evitar divisão por zero
            normalized_query_embeddings = query_embeddings / norms
            print("SearchService: Normalização concluída/verificada.")

            # 4. Realizar a Busca Vetorial
            search_k = k * 5 # Buscar um pouco mais para filtrar
            print(f"SearchService: Buscando {search_k} vizinhos mais próximos no índice FAISS (IndexFlatIP)...")
            # Assumindo agora que distances_sq contém DIRETAMENTE o produto interno (cosseno)
            distances_sq, indices = faiss_index.search(normalized_query_embeddings, search_k)
            print("SearchService: Busca FAISS concluída.")

            # 5. Processar Resultados e Filtrar por Tipo 'table'
            print("SearchService: Processando resultados e filtrando por tipo 'table'...")
            num_queries = query_embeddings.shape[0]
            for i in range(num_queries):
                query_table_name = query_table_names[i]
                query_result = {"query_table": query_table_name, "matches": []}
                found_matches_count = 0

                for j in range(search_k):
                    match_index = indices[i][j]
                    if match_index == -1:
                        continue

                    try:
                        match_metadata = metadata_list[match_index]
                    except IndexError:
                        print(f"SearchService WARNING: Índice {match_index} fora dos limites para metadados (Tamanho: {len(metadata_list)}). Pulando.")
                        continue

                    if match_metadata.get('type') == 'table':
                        schema = match_metadata.get('schema', 'unknown_schema')
                        table = match_metadata.get('name', 'unknown_table')
                        qualified_table_name = f"{schema}.{table}"

                        content_chunk = match_metadata.get('content')

                        if content_chunk:
                            # --- **** CORREÇÃO REVISADA APLICADA AQUI **** ---
                            # Assumimos que distances_sq contém o cosseno diretamente.
                            raw_cos_sim = distances_sq[i][j]

                            # Clamp (limitar) entre 0.0 e 1.0 para segurança
                            cos_sim = float(max(0.0, min(1.0, raw_cos_sim)))

                            # Porcentagem é cosseno * 100
                            similarity_percentage = float(round(cos_sim * 100, 2))
                            # --- **** FIM DA CORREÇÃO REVISADA **** ---

                            # Debug (opcional): Verificar os valores
                            # print(f"  Debug Match: Index {match_index}, Table: {qualified_table_name}, FAISS score (dist_sq/cos_sim): {distances_sq[i][j]:.4f}, Clamped CosSim: {cos_sim:.4f}, Perc: {similarity_percentage:.2f}%")

                            query_result["matches"].append({
                                "table_name": qualified_table_name,
                                "similarity_percentage": similarity_percentage,
                                "content": content_chunk
                            })
                            found_matches_count += 1

                            if found_matches_count >= k:
                                break
                        else:
                            print(f"SearchService WARNING: Conteúdo não encontrado nos metadados para a tabela '{qualified_table_name}' (índice {match_index}). Match ignorado.")

                if query_result["matches"]:
                    results.append(query_result)
                else:
                    print(f"SearchService: Nenhuma correspondência do tipo 'table' encontrada para a consulta '{query_table_name}' dentro dos {search_k} vizinhos.")
                    results.append({"query_table": query_table_name, "matches": []})

            print(f"SearchService: Processamento concluído. Retornando {len(results)} resultados de consulta.")
            return results

        except FileNotFoundError:
            print(f"SearchService ERROR: Arquivo de índice ({IndexLoader.FAISS_INDEX_PATH}) ou metadados ({IndexLoader.METADATA_PATH}) não encontrado.")
            return []
        except Exception as e:
            import traceback
            print(f"SearchService CRITICAL ERROR: Erro inesperado durante a busca: {e}")
            traceback.print_exc()
            return []