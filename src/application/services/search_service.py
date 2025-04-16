# src/infrastructure/vector_database/search_service.py
import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Tuple, Any
from src.infrastructure.persistence.index_loader import IndexLoader

class SearchService:
    """
    Serviço para buscar elementos similares (especificamente tabelas)
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
            Exemplo:
            [
                {
                    "query_table": "cliente",
                    "matches": [
                        {"table_name": "public.clientes", "similarity_percentage": 95.2},
                        {"table_name": "stage.stg_clientes", "similarity_percentage": 88.1},
                        # ... até k correspondências de TABELAS
                    ]
                },
                {
                    "query_table": "pedido",
                    "matches": [
                        {"table_name": "comercial.pedidos_venda", "similarity_percentage": 92.5},
                        {"table_name": "public.pedidos", "similarity_percentage": 90.0},
                    ] # Pode ter menos de k se não encontrar ou filtrar
                },
                # ... para cada tabela na consulta original
            ]
            Retorna uma lista vazia se ocorrer um erro ou nenhuma entrada for processada.
        """
        results = []
        faiss_index = None
        metadata_list = None

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
                # Considerar lançar uma exceção ou retornar erro mais explícito
                return []

            # 2. Verificar Dimensão do Embedding da Consulta
            query_dim = query_embeddings.shape[1]
            index_dim = faiss_index.d
            if query_dim != index_dim:
                print(f"SearchService ERROR: Dimensão do embedding da consulta ({query_dim}) não corresponde à dimensão do índice ({index_dim}).")
                return []

            # 3. Garantir Normalização L2 dos Embeddings da Consulta (IMPORTANTE!)
            # O script de criação normaliza antes de adicionar ao IndexFlatL2.
            # A busca com L2 funciona melhor (simula cosseno) se ambos os vetores (índice e consulta) estiverem normalizados.
            print("SearchService: Normalizando embeddings de consulta (L2 norm)...")
            norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
            # Evitar divisão por zero para vetores nulos (embora improvável para embeddings de texto)
            norms[norms == 0] = 1e-10
            normalized_query_embeddings = query_embeddings / norms
            print("SearchService: Normalização concluída.")

            # 4. Realizar a Busca Vetorial
            # O k para a busca FAISS precisa ser um pouco maior se filtrarmos depois,
            # para aumentar a chance de encontrar 'k' itens do tipo 'table'.
            search_k = k * 5000 # Buscar mais para ter margem para filtrar por tipo 'table'
            print(f"SearchService: Buscando {search_k} vizinhos mais próximos no índice FAISS...")
            # search retorna:
            # D: Distâncias (Squared L2 para IndexFlatL2) - shape (num_queries, search_k)
            # I: Índices dos vizinhos no metadata_list - shape (num_queries, search_k)
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

                    # FAISS pode retornar -1 se houver menos de 'search_k' itens no índice total
                    if match_index == -1:
                        continue

                    # Acessar metadados correspondentes
                    try:
                        match_metadata = metadata_list[match_index]
                    except IndexError:
                        print(f"SearchService WARNING: Índice {match_index} fora dos limites para metadados (Tamanho: {len(metadata_list)}). Pulando.")
                        continue

                    # --- FILTRAR: Queremos apenas correspondências do tipo 'table' ---
                    if match_metadata.get('type') == 'table':
                        # Extrair nome qualificado da tabela (schema.table)
                        schema = match_metadata.get('schema', 'unknown_schema')
                        table = match_metadata.get('name', 'unknown_table')
                        qualified_table_name = f"{schema}.{table}"

                        # Calcular similaridade
                        dist_sq = distances_sq[i][j]
                        # Garante que cos_sim seja float padrão
                        cos_sim = float(max(0.0, 1.0 - (dist_sq / 2.0)))
                        similarity_calc = cos_sim * 100

                        # Converte para float padrão ANTES de adicionar ao dicionário
                        similarity_percentage = float(round(similarity_calc, 2))

                        query_result["matches"].append({
                            "table_name": qualified_table_name,
                            "similarity_percentage": similarity_percentage # Agora é um float padrão
                            # ... (outros metadados se houver)
                        })
                        found_matches_count += 1

                        # Parar se já encontramos 'k' correspondências do TIPO TABELA
                        if found_matches_count >= k:
                            break

                # Adicionar o resultado desta consulta à lista geral
                if query_result["matches"]: # Adiciona apenas se encontrou alguma correspondência de tabela
                    results.append(query_result)
                else:
                    print(f"SearchService: Nenhuma correspondência do tipo 'table' encontrada para a consulta '{query_table_name}' dentro dos {search_k} vizinhos.")
                    # Opcionalmente, adicionar um resultado vazio para indicar que a busca foi feita
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
            return [] # Retorna lista vazia em caso de erro crítico